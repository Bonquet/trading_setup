//+------------------------------------------------------------------+
//|                                          XAU_AutoTrader_Tester.mq5 |
//|        STRATEGY TESTER VERSION — file-based signal input only      |
//|                                                                    |
//| Same trade-execution and management logic as XAU_AutoTrader.mq5    |
//| (BE at +1R, partial close at +1.5R, trail SL by 0.5xH1 ATR after   |
//| partial), BUT signals come from a LOCAL FILE in MQL5/Files/ instead |
//| of WebRequest. Works in Strategy Tester (WebRequest is blocked     |
//| there); use this to validate trade management before going live.   |
//|                                                                    |
//| For live trading, use XAU_AutoTrader.mq5 (the production version). |
//+------------------------------------------------------------------+
#property copyright "trading_setup"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/SymbolInfo.mqh>

//==================== Inputs ====================================//
input group "Signal Source (file-based — works in Strategy Tester)"
input string  Signal_File         = "test_signal_buy.json";   // file in MQL5/Files/
input int     Poll_Seconds        = 30;
input string  Symbol_Override     = "";                        // empty = chart symbol

input group "Risk"
input double  Risk_Percent        = 1.0;
input double  Max_Risk_USD        = 0.0;
input double  Min_Lot             = 0.01;
input double  Max_Lot             = 1.00;
input int     Max_Trades_Per_Day  = 5;
input int     Max_Open_Positions  = 1;

input group "Signal Filters"
input int     Max_Signal_Age_Sec  = 0;          // 0 = ignore age check (good for tester)
input bool    Take_Buy_Signals    = true;
input bool    Take_Sell_Signals   = true;

input group "Trade Management"
input double  BE_Trigger_R        = 1.0;
input double  BE_Buffer_Points    = 2.0;
input bool    Use_Partial_Close   = true;
input double  Partial_R           = 1.5;
input double  Partial_Percent     = 50.0;
input bool    Use_Trailing        = true;
input double  Trail_ATR_Mult      = 0.5;

input group "Identity"
input long    Magic_Number        = 4040406;    // different from production EA
input string  Trade_Comment       = "xau-tester";

//==================== Globals ===================================//
CTrade         g_trade;
CPositionInfo  g_pos;
CSymbolInfo    g_sym;

string         g_symbol;
string         g_last_signal_id   = "";
int            g_today_trades     = 0;
datetime       g_today_date       = 0;
datetime       g_last_poll        = 0;

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
      PrintFormat("[INIT] Symbol '%s' not found.", g_symbol);
      return INIT_FAILED;
   }
   g_sym.RefreshRates();
   g_trade.SetExpertMagicNumber(Magic_Number);
   g_trade.SetMarginMode();
   g_trade.SetTypeFillingBySymbol(g_symbol);
   g_trade.LogLevel(LOG_LEVEL_ERRORS);

   PrintFormat("[INIT] TESTER mode on %s | risk=%.1f%% | magic=%I64d | signal file: %s",
               g_symbol, Risk_Percent, Magic_Number, Signal_File);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {
   PrintFormat("[DEINIT] reason=%d", reason);
}

//==================== Tick (poll + manage) ======================//
void OnTick() {
   // Poll the signal file at most every Poll_Seconds, regardless of tick frequency
   if (TimeCurrent() - g_last_poll >= Poll_Seconds) {
      g_last_poll = TimeCurrent();
      ResetDailyCounterIfNewDay();
      if (CountMyOpenPositions() < Max_Open_Positions && g_today_trades < Max_Trades_Per_Day) {
         string json = ReadSignalFile();
         if (json != "") ProcessSignal(json);
      }
   }
   ManageOpenPositions();
}

//==================== Signal file read ==========================//
string ReadSignalFile() {
   int flags = FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ;
   int h = FileOpen(Signal_File, flags);
   if (h == INVALID_HANDLE) {
      static datetime last_warn = 0;
      if (TimeCurrent() - last_warn > 120) {
         PrintFormat("[FILE] '%s' not found in MQL5/Files/", Signal_File);
         last_warn = TimeCurrent();
      }
      return "";
   }
   string content = "";
   while (!FileIsEnding(h)) content += FileReadString(h) + "\n";
   FileClose(h);
   return content;
}

//==================== JSON helpers ==============================//
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
double JsonNum(string json, string key) { return StringToDouble(JsonStr(json, key)); }

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

   double sig_entry = JsonNum(json, "entry");
   double sl        = JsonNum(json, "stop_loss");
   double tp_final  = JsonNum(json, "tp2");
   if (sig_entry <= 0 || sl <= 0 || tp_final <= 0) {
      PrintFormat("[SKIP] invalid prices entry=%.2f sl=%.2f tp=%.2f", sig_entry, sl, tp_final);
      g_last_signal_id = signal_id;
      return;
   }

   g_sym.RefreshRates();
   double entry_now = (direction == "BUY") ? g_sym.Ask() : g_sym.Bid();
   double stop_distance = MathAbs(entry_now - sl);
   if (stop_distance <= 0) return;

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
         RegisterPosition(ticket, g_pos.PriceOpen(), g_pos.StopLoss(), g_pos.Volume(),
                          MathAbs(g_pos.PriceOpen() - g_pos.StopLoss()));
         sidx = FindStateIdx(ticket);
         if (sidx < 0) continue;
      }

      double entry        = g_states[sidx].original_entry;
      double original_risk= g_states[sidx].original_risk;
      bool   is_buy       = (g_pos.PositionType() == POSITION_TYPE_BUY);

      g_sym.RefreshRates();
      double price = is_buy ? g_sym.Bid() : g_sym.Ask();
      double favorable = is_buy ? (price - entry) : (entry - price);
      double r_multiple = (original_risk > 0) ? favorable / original_risk : 0;

      if (!g_states[sidx].be_done && r_multiple >= BE_Trigger_R) {
         double buf = BE_Buffer_Points * g_sym.Point();
         double new_sl = is_buy ? entry + buf : entry - buf;
         if (g_trade.PositionModify(ticket, new_sl, g_pos.TakeProfit())) {
            g_states[sidx].be_done = true;
            PrintFormat("[BE] ticket=%I64u SL->BE %.2f at +%.2fR", ticket, new_sl, r_multiple);
         }
      }

      if (Use_Partial_Close && !g_states[sidx].partial_done && r_multiple >= Partial_R) {
         double close_vol = NormalizeVolume(g_pos.Volume() * (Partial_Percent / 100.0));
         if (close_vol >= g_sym.LotsMin() && close_vol < g_pos.Volume()) {
            if (g_trade.PositionClosePartial(ticket, close_vol)) {
               g_states[sidx].partial_done = true;
               PrintFormat("[PARTIAL] ticket=%I64u closed %.2f at +%.2fR", ticket, close_vol, r_multiple);
            }
         }
      }

      if (Use_Trailing && g_states[sidx].partial_done) {
         int atr_handle = iATR(g_symbol, PERIOD_H1, 14);
         double atr_val[];
         ArraySetAsSeries(atr_val, true);
         if (CopyBuffer(atr_handle, 0, 0, 1, atr_val) > 0) {
            double trail_dist = atr_val[0] * Trail_ATR_Mult;
            double new_sl = is_buy ? price - trail_dist : price + trail_dist;
            double cur_sl = g_pos.StopLoss();
            bool improves = is_buy ? (new_sl > cur_sl) : (new_sl < cur_sl);
            if (improves) g_trade.PositionModify(ticket, new_sl, g_pos.TakeProfit());
         }
      }
   }
}

//==================== Helpers ===================================//
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
   TimeToStruct(TimeCurrent(), dt);
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
//+------------------------------------------------------------------+
