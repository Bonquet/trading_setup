//+------------------------------------------------------------------+
//|                                                XAU_AutoTrader.mq5 |
//|                 Auto-executor for github.com/Bonquet/trading_setup |
//|                                                                    |
//| Polls GitHub raw URL for signals → opens market orders with the    |
//| signal's SL/TP → manages position (BE at +1R, partial at +1.5R,    |
//| trail SL after partial). Reads CURRENT MT5 balance for sizing.     |
//+------------------------------------------------------------------+
#property copyright "trading_setup"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/SymbolInfo.mqh>

//==================== Inputs ====================================//
input group "Connection"
input string  Signal_URL          = "https://raw.githubusercontent.com/Bonquet/trading_setup/main/data/signals/latest.json";
input int     Poll_Seconds        = 30;
input string  Symbol_Override     = "";        // empty = chart symbol (XAUUSD, GOLD, XAUUSD.r, etc.)
input string  Test_Mode_File      = "";        // If set, read signals from MQL5/Files/<this> instead of URL. Works in Strategy Tester. e.g. "test_signal.json"

input group "Risk"
input double  Risk_Percent        = 1.0;       // % of balance to risk per trade
input double  Max_Risk_USD        = 0.0;       // hard $ cap (0 = no cap)
input double  Min_Lot             = 0.01;      // minimum lot to bother trading
input double  Max_Lot             = 1.00;      // safety max
input int     Max_Trades_Per_Day  = 5;
input int     Max_Open_Positions  = 1;          // for THIS EA's magic number

input group "Signal Filters"
input int     Max_Signal_Age_Sec  = 1800;       // skip if signal older than this
input bool    Take_Buy_Signals    = true;
input bool    Take_Sell_Signals   = true;
input string  Required_Styles     = "swing,intraday,scalp";  // CSV; empty = all

input group "Trade Management"
input double  BE_Trigger_R        = 1.0;        // R multiple to move SL to break-even
input double  BE_Buffer_Points    = 2.0;        // small buffer past entry (spread cover)
input bool    Use_Partial_Close   = true;
input double  Partial_R           = 1.5;        // R multiple to close partial
input double  Partial_Percent     = 50.0;       // % of position to close
input bool    Use_Trailing        = true;
input double  Trail_ATR_Mult      = 0.5;        // trail by N × H1 ATR after partial

input group "Identity"
input long    Magic_Number        = 4040405;
input string  Trade_Comment       = "xau-autotrader";

//==================== Globals ===================================//
CTrade         g_trade;
CPositionInfo  g_pos;
CSymbolInfo    g_sym;

string         g_symbol;
datetime       g_last_poll        = 0;
string         g_last_signal_id   = "";
int            g_today_trades     = 0;
datetime       g_today_date       = 0;

// Per-position state (keyed by ticket via comment hashing or just by checking SL position)
// We track:  ticket -> { be_done, partial_done, original_sl, original_risk }
struct PosState {
   ulong  ticket;
   bool   be_done;
   bool   partial_done;
   double original_sl;
   double original_risk;
   double original_entry;
   double original_lots;
};
PosState g_states[];

//==================== OnInit ====================================//
int OnInit() {
   g_symbol = (Symbol_Override == "") ? _Symbol : Symbol_Override;
   if (!g_sym.Name(g_symbol)) {
      PrintFormat("[INIT] Symbol '%s' not found. Set Symbol_Override.", g_symbol);
      return INIT_FAILED;
   }
   g_sym.RefreshRates();
   g_trade.SetExpertMagicNumber(Magic_Number);
   g_trade.SetMarginMode();
   g_trade.SetTypeFillingBySymbol(g_symbol);
   g_trade.LogLevel(LOG_LEVEL_ERRORS);

   if (!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) {
      Print("[INIT] AutoTrading disabled in terminal. Click the AutoTrading button.");
   }
   LoadStateFromFile();
   EventSetTimer(MathMax(5, Poll_Seconds));
   PrintFormat("[INIT] XAU AutoTrader live on %s | risk=%.1f%% | poll=%ds | magic=%I64d",
               g_symbol, Risk_Percent, Poll_Seconds, Magic_Number);
   PrintFormat("[INIT] Signal source: %s", Signal_URL);
   PrintFormat("[INIT] If WebRequest fails, add the URL host in:");
   Print("       Tools -> Options -> Expert Advisors -> 'Allow WebRequest for listed URL'");
   Print("       Add: https://raw.githubusercontent.com");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {
   EventKillTimer();
   SaveStateToFile();
   PrintFormat("[DEINIT] reason=%d", reason);
}

//==================== Timer (signal poll) =======================//
void OnTimer() {
   ResetDailyCounterIfNewDay();
   if (CountMyOpenPositions() >= Max_Open_Positions) return;
   if (g_today_trades >= Max_Trades_Per_Day) return;

   string json = FetchSignalJSON();
   if (json == "") return;
   ProcessSignal(json);
}

//==================== Tick (trade management) ===================//
void OnTick() {
   ManageOpenPositions();
}

//==================== Signal fetch ==============================//
string FetchSignalJSON() {
   // Test mode — read from local file. Works in Strategy Tester (WebRequest doesn't).
   if (Test_Mode_File != "") return ReadFileSignal();

   char data[];
   char result[];
   string result_headers;
   ResetLastError();
   int timeout = 5000;
   int code = WebRequest("GET", Signal_URL, "", "", timeout, data, 0, result, result_headers);
   if (code == -1) {
      int err = GetLastError();
      if (err == 4014) {
         // ERR_FUNCTION_NOT_ALLOWED. Two causes:
         // 1. Strategy Tester (WebRequest is permanently blocked there)
         // 2. Live: 'Allow WebRequest for listed URL' unticked entirely
         if (MQLInfoInteger(MQL_TESTER)) {
            Print("[FETCH] You are in the Strategy Tester — WebRequest is BLOCKED here.");
            Print("        Set Test_Mode_File input to a filename in MQL5/Files/ to test.");
         } else {
            Print("[FETCH] WebRequest is disabled. Open MT5 Tools -> Options -> Expert Advisors,");
            Print("        tick 'Allow WebRequest for listed URL', add https://raw.githubusercontent.com");
         }
      } else if (err == 4060) {
         PrintFormat("[FETCH] URL not in the allowed list: %s", Signal_URL);
         Print("        Add https://raw.githubusercontent.com under Tools -> Options -> Expert Advisors");
      } else {
         PrintFormat("[FETCH] WebRequest error %d on %s", err, Signal_URL);
      }
      return "";
   }
   if (code != 200) {
      PrintFormat("[FETCH] HTTP %d", code);
      return "";
   }
   return CharArrayToString(result, 0, -1, CP_UTF8);
}

string ReadFileSignal() {
   // Read MQL5/Files/<Test_Mode_File>. Returns "" on failure.
   int flags = FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ;
   int h = FileOpen(Test_Mode_File, flags);
   if (h == INVALID_HANDLE) {
      static datetime last_warn = 0;
      if (TimeCurrent() - last_warn > 60) {
         PrintFormat("[FETCH] Test_Mode_File '%s' not found in MQL5/Files/. err=%d",
                     Test_Mode_File, GetLastError());
         last_warn = TimeCurrent();
      }
      return "";
   }
   string content = "";
   while (!FileIsEnding(h)) content += FileReadString(h) + "\n";
   FileClose(h);
   return content;
}

//==================== JSON helpers (string scan; only what we need) =====//
// Extract a string field by key. Handles "key": "value" patterns.
string JsonStr(string json, string key) {
   string pat = "\"" + key + "\"";
   int p = StringFind(json, pat);
   if (p < 0) return "";
   p = StringFind(json, ":", p);
   if (p < 0) return "";
   p++;
   while (p < StringLen(json)) {
      ushort c = StringGetCharacter(json, p);
      if (c == ' ' || c == '\n' || c == '\r' || c == '\t') { p++; continue; }
      break;
   }
   if (p >= StringLen(json)) return "";
   if (StringGetCharacter(json, p) == '"') p++;
   int end = StringFind(json, "\"", p);
   if (end < 0) {
      int e1 = StringFind(json, ",", p);
      int e2 = StringFind(json, "}", p);
      end = (e1 >= 0 && (e2 < 0 || e1 < e2)) ? e1 : e2;
   }
   if (end < 0) return "";
   return StringSubstr(json, p, end - p);
}
double JsonNum(string json, string key) {
   string v = JsonStr(json, key);
   return StringToDouble(v);
}

//==================== Process incoming signal ===================//
void ProcessSignal(string json) {
   string decision = JsonStr(json, "decision");
   if (decision != "Valid Trade") return;

   string signal_id = JsonStr(json, "signal_id");
   if (signal_id == "") signal_id = JsonStr(json, "published_at_utc");
   if (signal_id == "") signal_id = JsonStr(json, "fetched_at_utc");
   if (signal_id == g_last_signal_id) return;

   string direction = JsonStr(json, "direction");
   StringToUpper(direction);
   if (direction != "BUY" && direction != "SELL") return;
   if (direction == "BUY"  && !Take_Buy_Signals)  return;
   if (direction == "SELL" && !Take_Sell_Signals) return;

   // Style filter
   if (Required_Styles != "") {
      string style = JsonStr(json, "style");
      if (StringFind("," + Required_Styles + ",", "," + style + ",") < 0) {
         PrintFormat("[SKIP] style '%s' not in required list", style);
         g_last_signal_id = signal_id;  // mark seen so we don't recheck
         return;
      }
   }

   // Freshness
   string published = JsonStr(json, "published_at_utc");
   if (published == "") published = JsonStr(json, "fetched_at_utc");
   datetime pub_dt = ParseISO8601(published);
   if (pub_dt > 0) {
      int age = (int)(TimeGMT() - pub_dt);
      if (age > Max_Signal_Age_Sec) {
         PrintFormat("[SKIP] signal age %ds > max %ds", age, Max_Signal_Age_Sec);
         g_last_signal_id = signal_id;
         return;
      }
   }

   double sig_entry = JsonNum(json, "entry");
   double sl        = JsonNum(json, "stop_loss");
   double tp_final  = JsonNum(json, "tp2");
   double tp1       = JsonNum(json, "tp1");
   if (sig_entry <= 0 || sl <= 0 || tp_final <= 0) {
      PrintFormat("[SKIP] invalid prices entry=%.2f sl=%.2f tp=%.2f", sig_entry, sl, tp_final);
      g_last_signal_id = signal_id;
      return;
   }

   // Use current market price (not the signal's snapshot — it may have moved)
   g_sym.RefreshRates();
   double entry_now = (direction == "BUY") ? g_sym.Ask() : g_sym.Bid();
   double stop_distance = MathAbs(entry_now - sl);
   if (stop_distance <= 0) return;

   // Lot sizing from CURRENT MT5 balance
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amt = balance * Risk_Percent / 100.0;
   if (Max_Risk_USD > 0 && risk_amt > Max_Risk_USD) risk_amt = Max_Risk_USD;

   double tick_value = g_sym.TickValue();
   double tick_size  = g_sym.TickSize();
   if (tick_value <= 0 || tick_size <= 0) {
      Print("[SKIP] bad symbol tick info");
      g_last_signal_id = signal_id;
      return;
   }
   double risk_per_lot = (stop_distance / tick_size) * tick_value;
   double lots = (risk_per_lot > 0) ? risk_amt / risk_per_lot : 0;

   double vol_step = g_sym.LotsStep();
   double vol_min  = g_sym.LotsMin();
   double vol_max  = g_sym.LotsMax();
   lots = MathFloor(lots / vol_step) * vol_step;
   lots = MathMax(vol_min, MathMin(vol_max, lots));
   lots = MathMax(Min_Lot, MathMin(Max_Lot, lots));

   double final_risk = (stop_distance / tick_size) * tick_value * lots;
   PrintFormat("[OPEN] %s %s @ %.2f SL=%.2f TP=%.2f lots=%.2f risk=$%.2f bal=$%.2f sid=%s",
               direction, g_symbol, entry_now, sl, tp_final, lots, final_risk, balance, signal_id);

   bool ok = false;
   string comment = Trade_Comment + ":" + signal_id;
   if (direction == "BUY") {
      ok = g_trade.Buy(lots, g_symbol, 0, sl, tp_final, comment);
   } else {
      ok = g_trade.Sell(lots, g_symbol, 0, sl, tp_final, comment);
   }
   if (!ok) {
      PrintFormat("[OPEN FAIL] retcode=%d msg=%s",
                  g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription());
      return;
   }
   ulong ticket = g_trade.ResultOrder();
   RegisterPosition(ticket, entry_now, sl, lots, stop_distance);
   g_last_signal_id = signal_id;
   g_today_trades++;
   SaveStateToFile();
}

//==================== Trade management ==========================//
void ManageOpenPositions() {
   int total = PositionsTotal();
   for (int i = total - 1; i >= 0; i--) {
      if (!g_pos.SelectByIndex(i)) continue;
      if (g_pos.Magic() != Magic_Number) continue;
      if (g_pos.Symbol() != g_symbol) continue;

      ulong ticket = g_pos.Ticket();
      int   sidx   = FindStateIdx(ticket);
      if (sidx < 0) {
         // First time seeing this position — register from current state
         RegisterPosition(ticket, g_pos.PriceOpen(), g_pos.StopLoss(), g_pos.Volume(),
                          MathAbs(g_pos.PriceOpen() - g_pos.StopLoss()));
         sidx = FindStateIdx(ticket);
         if (sidx < 0) continue;
      }

      double entry        = g_states[sidx].original_entry;
      double original_sl  = g_states[sidx].original_sl;
      double original_risk= g_states[sidx].original_risk;
      bool   is_buy       = (g_pos.PositionType() == POSITION_TYPE_BUY);

      g_sym.RefreshRates();
      double price = is_buy ? g_sym.Bid() : g_sym.Ask();
      double favorable = is_buy ? (price - entry) : (entry - price);
      double r_multiple = (original_risk > 0) ? favorable / original_risk : 0;

      // 1. Move to break-even at +BE_Trigger_R
      if (!g_states[sidx].be_done && r_multiple >= BE_Trigger_R) {
         double buf = BE_Buffer_Points * g_sym.Point();
         double new_sl = is_buy ? entry + buf : entry - buf;
         if (g_trade.PositionModify(ticket, new_sl, g_pos.TakeProfit())) {
            g_states[sidx].be_done = true;
            PrintFormat("[BE] ticket=%I64u moved SL to BE %.2f at +%.2fR", ticket, new_sl, r_multiple);
            SaveStateToFile();
         }
      }

      // 2. Partial close at +Partial_R
      if (Use_Partial_Close && !g_states[sidx].partial_done && r_multiple >= Partial_R) {
         double close_vol = NormalizeVolume(g_pos.Volume() * (Partial_Percent / 100.0));
         if (close_vol >= g_sym.LotsMin() && close_vol < g_pos.Volume()) {
            if (g_trade.PositionClosePartial(ticket, close_vol)) {
               g_states[sidx].partial_done = true;
               PrintFormat("[PARTIAL] ticket=%I64u closed %.2f at +%.2fR", ticket, close_vol, r_multiple);
               SaveStateToFile();
            }
         }
      }

      // 3. Trail SL after partial close
      if (Use_Trailing && g_states[sidx].partial_done) {
         double atr = iATR(g_symbol, PERIOD_H1, 14);
         double atr_val[];
         ArraySetAsSeries(atr_val, true);
         if (CopyBuffer((int)atr, 0, 0, 1, atr_val) > 0) {
            double trail_dist = atr_val[0] * Trail_ATR_Mult;
            double new_sl = is_buy ? price - trail_dist : price + trail_dist;
            double cur_sl = g_pos.StopLoss();
            bool improves = is_buy ? (new_sl > cur_sl) : (new_sl < cur_sl);
            if (improves) {
               g_trade.PositionModify(ticket, new_sl, g_pos.TakeProfit());
            }
         }
      }
   }
}

//==================== State helpers =============================//
int FindStateIdx(ulong ticket) {
   for (int i = 0; i < ArraySize(g_states); i++)
      if (g_states[i].ticket == ticket) return i;
   return -1;
}

void RegisterPosition(ulong ticket, double entry, double sl, double lots, double risk) {
   int i = ArraySize(g_states);
   ArrayResize(g_states, i + 1);
   g_states[i].ticket = ticket;
   g_states[i].be_done = false;
   g_states[i].partial_done = false;
   g_states[i].original_sl = sl;
   g_states[i].original_risk = (risk > 0) ? risk : MathAbs(entry - sl);
   g_states[i].original_entry = entry;
   g_states[i].original_lots = lots;
}

int CountMyOpenPositions() {
   int count = 0;
   for (int i = 0; i < PositionsTotal(); i++) {
      if (!g_pos.SelectByIndex(i)) continue;
      if (g_pos.Magic() == Magic_Number && g_pos.Symbol() == g_symbol) count++;
   }
   return count;
}

void ResetDailyCounterIfNewDay() {
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   datetime today_at_midnight = StringToTime(StringFormat("%04d.%02d.%02d 00:00", dt.year, dt.mon, dt.day));
   if (g_today_date != today_at_midnight) {
      g_today_date = today_at_midnight;
      g_today_trades = 0;
   }
}

double NormalizeVolume(double vol) {
   double step = g_sym.LotsStep();
   if (step <= 0) step = 0.01;
   vol = MathFloor(vol / step) * step;
   double min_v = g_sym.LotsMin();
   double max_v = g_sym.LotsMax();
   vol = MathMax(min_v, MathMin(max_v, vol));
   return vol;
}

datetime ParseISO8601(string s) {
   // Accepts YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+00:00
   if (StringLen(s) < 19) return 0;
   int y = (int)StringToInteger(StringSubstr(s, 0, 4));
   int mo = (int)StringToInteger(StringSubstr(s, 5, 2));
   int d = (int)StringToInteger(StringSubstr(s, 8, 2));
   int h = (int)StringToInteger(StringSubstr(s, 11, 2));
   int mi = (int)StringToInteger(StringSubstr(s, 14, 2));
   int sec = (int)StringToInteger(StringSubstr(s, 17, 2));
   if (y == 0) return 0;
   return StringToTime(StringFormat("%04d.%02d.%02d %02d:%02d:%02d", y, mo, d, h, mi, sec));
}

//==================== Persistent state on disk ==================//
string StateFilename() { return "xau_autotrader_state.txt"; }

void SaveStateToFile() {
   int h = FileOpen(StateFilename(), FILE_WRITE | FILE_TXT | FILE_ANSI);
   if (h == INVALID_HANDLE) return;
   FileWriteString(h, "last_signal_id=" + g_last_signal_id + "\n");
   FileWriteString(h, "today_date=" + IntegerToString((long)g_today_date) + "\n");
   FileWriteString(h, "today_trades=" + IntegerToString(g_today_trades) + "\n");
   FileClose(h);
}

void LoadStateFromFile() {
   if (!FileIsExist(StateFilename())) return;
   int h = FileOpen(StateFilename(), FILE_READ | FILE_TXT | FILE_ANSI);
   if (h == INVALID_HANDLE) return;
   while (!FileIsEnding(h)) {
      string line = FileReadString(h);
      int eq = StringFind(line, "=");
      if (eq < 0) continue;
      string k = StringSubstr(line, 0, eq);
      string v = StringSubstr(line, eq + 1);
      StringTrimRight(v);
      if (k == "last_signal_id") g_last_signal_id = v;
      else if (k == "today_date") g_today_date = (datetime)StringToInteger(v);
      else if (k == "today_trades") g_today_trades = (int)StringToInteger(v);
   }
   FileClose(h);
   PrintFormat("[STATE] loaded last_signal_id=%s today_trades=%d",
               g_last_signal_id, g_today_trades);
}
//+------------------------------------------------------------------+
