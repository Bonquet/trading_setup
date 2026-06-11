//+------------------------------------------------------------------+
//|                                          XAU_AutoTrader_Tester.mq5 |
//|        STRATEGY TESTER VERSION — self-contained synthetic signals  |
//|                                                                    |
//| Validates the trade-management logic (BE at +1R, partial 50% at    |
//| +1.5R, trail SL by 0.5x H1 ATR) without depending on any external  |
//| file or network. Generates synthetic signals internally — alternates|
//| BUY/SELL by default so both sides are tested.                      |
//|                                                                    |
//| For live trading, use XAU_AutoTrader.mq5 (production WebRequest).  |
//+------------------------------------------------------------------+
#property copyright "trading_setup"
#property version   "2.00"
#property strict

#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/SymbolInfo.mqh>

//==================== Inputs ====================================//
input group "Signal generator (internal — no file needed)"
input string  Direction_Mode      = "Alternating";   // "Alternating" | "Random" | "BuyOnly" | "SellOnly"
input int     Re_Trigger_Hours    = 24;              // how often to open a new test trade
input bool    Use_ATR_Stop        = true;            // if true, SL = ATR_Mult x H1 ATR (volatility-adaptive); if false, use fixed Stop_Distance_Dollars
input double  ATR_Mult            = 1.5;             // when Use_ATR_Stop=true; 1.5x H1 ATR is typical swing stop
input double  Stop_Distance_Dollars = 20.0;          // when Use_ATR_Stop=false; direct $ distance (e.g. 20.0 = $20 stop on XAU)
input double  TP_R_Multiple       = 2.0;             // TP at this R multiple of stop

input group "Risk"
input double  Risk_Percent        = 1.0;
input double  Min_Lot             = 0.01;
input double  Max_Lot             = 1.00;
input int     Max_Trades_Per_Day  = 5;
input int     Max_Open_Positions  = 1;
input string  Symbol_Override     = "";

input group "Trade Management"
input double  BE_Trigger_R        = 1.0;
input double  BE_Buffer_Points    = 2.0;
input bool    Use_Partial_Close   = true;
input double  Partial_R           = 1.5;
input double  Partial_Percent     = 50.0;
input bool    Use_Trailing        = true;
input double  Trail_ATR_Mult      = 0.5;

input group "Identity"
input long    Magic_Number        = 4040406;          // separate from production EA
input string  Trade_Comment       = "xau-tester";

//==================== Globals ===================================//
CTrade         g_trade;
CPositionInfo  g_pos;
CSymbolInfo    g_sym;

string         g_symbol;
int            g_today_trades     = 0;
datetime       g_today_date       = 0;
datetime       g_last_trigger_at  = 0;
int            g_alternating_idx  = 0;  // 0 = BUY, 1 = SELL, then flip

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

   PrintFormat("[INIT] TESTER mode on %s | risk=%.1f%% | magic=%I64d | dir_mode=%s | trigger=%dh",
               g_symbol, Risk_Percent, Magic_Number, Direction_Mode, Re_Trigger_Hours);
   PrintFormat("[INIT] Stop=%s, TP=%.1fR",
               Use_ATR_Stop ? StringFormat("%.1fx H1 ATR", ATR_Mult)
                            : StringFormat("$%.2f flat", Stop_Distance_Dollars),
               TP_R_Multiple);
   PrintFormat("[INIT] Trade mgmt: BE@+%.1fR | Partial %.0f%% @+%.1fR | Trail %.1fxATR after partial",
               BE_Trigger_R, Partial_Percent, Partial_R, Trail_ATR_Mult);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {
   PrintFormat("[DEINIT] reason=%d  total_trades_today=%d", reason, g_today_trades);
}

//==================== Tick =====================================//
void OnTick() {
   ResetDailyCounterIfNewDay();
   // Try to open a new test trade
   if (CanOpenNewTrade()) TryOpenTrade();
   // Manage anything open
   ManageOpenPositions();
}

//==================== Trade trigger =============================//
bool CanOpenNewTrade() {
   if (CountMyOpenPositions() >= Max_Open_Positions) return false;
   if (g_today_trades >= Max_Trades_Per_Day) return false;
   if (Re_Trigger_Hours > 0 && g_last_trigger_at > 0) {
      int hours_since = (int)((TimeCurrent() - g_last_trigger_at) / 3600);
      if (hours_since < Re_Trigger_Hours) return false;
   }
   return true;
}

void TryOpenTrade() {
   // Pick direction
   string dir = PickDirection();
   if (dir == "") return;

   g_sym.RefreshRates();
   double point = g_sym.Point();
   double entry_now = (dir == "BUY") ? g_sym.Ask() : g_sym.Bid();

   // Compute stop distance in PRICE units ($ on XAU)
   double stop_distance;
   if (Use_ATR_Stop) {
      double atr = GetH1ATR();
      if (atr <= 0) {
         Print("[SKIP] H1 ATR not ready yet");
         return;
      }
      stop_distance = atr * ATR_Mult;
   } else {
      stop_distance = Stop_Distance_Dollars;  // direct $ value (e.g. 20.0 = $20 stop on XAU)
   }
   if (stop_distance <= 0) return;

   // Sanity check: stop must respect broker's minimum stop distance
   double min_stop_price = g_sym.StopsLevel() * g_sym.Point();
   if (min_stop_price > 0 && stop_distance < min_stop_price) {
      PrintFormat("[SKIP] stop $%.2f below broker minimum $%.2f. Increase Stop_Distance_Dollars or ATR_Mult.",
                  stop_distance, min_stop_price);
      return;
   }

   double sl       = (dir == "BUY") ? entry_now - stop_distance : entry_now + stop_distance;
   double tp_final = (dir == "BUY") ? entry_now + stop_distance * TP_R_Multiple
                                    : entry_now - stop_distance * TP_R_Multiple;

   // Lot size from current balance
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amt = balance * Risk_Percent / 100.0;
   double tick_value = g_sym.TickValue();
   double tick_size  = g_sym.TickSize();
   if (tick_value <= 0 || tick_size <= 0) {
      Print("[SKIP] bad symbol tick info — symbol not loaded properly");
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
   PrintFormat("[OPEN] %s %s @ %.2f SL=%.2f TP=%.2f lots=%.2f risk=$%.2f bal=$%.2f",
               dir, g_symbol, entry_now, sl, tp_final, lots, final_risk, balance);

   bool ok = false;
   if (dir == "BUY") {
      ok = g_trade.Buy(lots, g_symbol, 0, sl, tp_final, Trade_Comment);
   } else {
      ok = g_trade.Sell(lots, g_symbol, 0, sl, tp_final, Trade_Comment);
   }
   if (!ok) {
      PrintFormat("[OPEN FAIL] %s retcode=%d msg=%s | lots=%.2f sl=%.2f tp=%.2f",
                  dir, g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription(),
                  lots, sl, tp_final);
      return;
   }
   ulong ticket = g_trade.ResultOrder();
   RegisterPosition(ticket, entry_now, sl, lots, stop_distance);
   g_last_trigger_at = TimeCurrent();
   g_today_trades++;
}

string PickDirection() {
   string mode = Direction_Mode;
   StringToLower(mode);
   if (mode == "buyonly")  return Use_Buy() ? "BUY" : "";
   if (mode == "sellonly") return Use_Sell() ? "SELL" : "";
   if (mode == "random") {
      MathSrand((int)TimeCurrent());
      bool buy = (MathRand() % 2) == 0;
      if (buy && Use_Buy())   return "BUY";
      if (!buy && Use_Sell()) return "SELL";
      // fallback to whichever is allowed
      if (Use_Buy())  return "BUY";
      if (Use_Sell()) return "SELL";
      return "";
   }
   // Default: alternating
   string pick;
   if (g_alternating_idx == 0) pick = "BUY"; else pick = "SELL";
   g_alternating_idx = 1 - g_alternating_idx;
   if (pick == "BUY"  && !Use_Buy())  pick = (Use_Sell() ? "SELL" : "");
   if (pick == "SELL" && !Use_Sell()) pick = (Use_Buy()  ? "BUY"  : "");
   return pick;
}

bool Use_Buy()  { return true; }   // could be input-controlled later
bool Use_Sell() { return true; }

double GetH1ATR() {
   int handle = iATR(g_symbol, PERIOD_H1, 14);
   if (handle == INVALID_HANDLE) return 0;
   double buf[];
   ArraySetAsSeries(buf, true);
   if (CopyBuffer(handle, 0, 0, 1, buf) <= 0) return 0;
   return buf[0];
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

      // 1. BE
      if (!g_states[sidx].be_done && r_multiple >= BE_Trigger_R) {
         double buf = BE_Buffer_Points * g_sym.Point();
         double new_sl = is_buy ? entry + buf : entry - buf;
         if (g_trade.PositionModify(ticket, new_sl, g_pos.TakeProfit())) {
            g_states[sidx].be_done = true;
            PrintFormat("[BE] ticket=%I64u SL->BE %.2f at +%.2fR", ticket, new_sl, r_multiple);
         }
      }

      // 2. Partial
      if (Use_Partial_Close && !g_states[sidx].partial_done && r_multiple >= Partial_R) {
         double close_vol = NormalizeVolume(g_pos.Volume() * (Partial_Percent / 100.0));
         if (close_vol >= g_sym.LotsMin() && close_vol < g_pos.Volume()) {
            if (g_trade.PositionClosePartial(ticket, close_vol)) {
               g_states[sidx].partial_done = true;
               PrintFormat("[PARTIAL] ticket=%I64u closed %.2f at +%.2fR", ticket, close_vol, r_multiple);
            }
         }
      }

      // 3. Trail
      if (Use_Trailing && g_states[sidx].partial_done) {
         double atr = GetH1ATR();
         if (atr > 0) {
            double trail_dist = atr * Trail_ATR_Mult;
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
