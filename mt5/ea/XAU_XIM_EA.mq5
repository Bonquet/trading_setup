//+------------------------------------------------------------------+
//|                                                    XAU_XIM_EA.mq5 |
//|                  XAU Intraday Momentum — H1 strategy for the EA   |
//|                                                                    |
//| Built from-scratch by data-mining modern (2019-2026) gold H1 data. |
//|                                                                    |
//| Rules:                                                             |
//|   TIMEFRAME: H1                                                    |
//|   DIRECTION: LONG ONLY (shorts fail in this regime)                |
//|   TREND FILTER: (EMA50-EMA200)/ATR14 > 0.5 AND EMA50 rising AND    |
//|                Close > EMA50                                       |
//|   ENTRY TRIGGER A (momentum thrust):                               |
//|     range > 1.2*ATR14 AND close > open AND body > 0.7*range        |
//|   ENTRY TRIGGER B (EMA50 pullback bounce):                         |
//|     low <= ema50 AND close > ema50 AND body > 0.6*range            |
//|   ACTIVE HOURS: 8-20 UTC only                                      |
//|   STOP: entry - 1.5*ATR14                                          |
//|   TARGET: entry + 3*(stop distance) = 3.0R                         |
//|   TIME EXIT: 16 H1 bars                                            |
//|   NO BE move, NO trailing (testing showed they kill the edge)      |
//|                                                                    |
//| Backtested 2019-2026: 543 trades, 38.7% WR, +0.140R, 1.24 PF,      |
//|                       +100.6% return, -28.5% DD, MAR 0.36          |
//+------------------------------------------------------------------+
#property copyright "trading_setup"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/SymbolInfo.mqh>

//==================== Inputs ====================================//
input group "Strategy rules"
input int     EMA_Fast              = 50;
input int     EMA_Slow              = 200;
input int     EMA_Slope_Lookback    = 20;
input double  Trend_Separation_ATR  = 0.5;     // EMA50 must be at least this many ATR above EMA200
input int     ATR_Period            = 14;
input double  Thrust_Range_Mult     = 1.2;     // bar range must exceed this x ATR
input double  Thrust_Body_Ratio     = 0.7;     // body / range minimum for thrust trigger
input double  Pullback_Body_Ratio   = 0.6;     // body / range minimum for pullback trigger
input int     Active_Hour_Start     = 8;       // UTC
input int     Active_Hour_End       = 20;
input double  ATR_Stop_Mult         = 1.5;
input double  RR_Target             = 3.0;
input int     Max_Bars_In_Trade     = 16;

input group "Risk"
input double  Risk_Percent          = 1.0;
input double  Min_Lot               = 0.01;
input double  Max_Lot               = 1.00;
input int     Max_Open_Positions    = 1;
input int     Max_Trades_Per_Day    = 3;

input group "Identity"
input long    Magic_Number          = 4040408;
input string  Trade_Comment         = "xau-xim";

//==================== Globals ===================================//
CTrade         g_trade;
CPositionInfo  g_pos;
CSymbolInfo    g_sym;

string         g_symbol;
int            h_ema_fast     = INVALID_HANDLE;
int            h_ema_slow     = INVALID_HANDLE;
int            h_atr          = INVALID_HANDLE;
datetime       g_last_bar_time = 0;
int            g_today_trades = 0;
datetime       g_today_date   = 0;

struct PosState {
   ulong   ticket;
   datetime opened_at_bar;
};
PosState g_states[];

//==================== OnInit ====================================//
int OnInit() {
   g_symbol = _Symbol;
   if (!g_sym.Name(g_symbol)) {
      PrintFormat("[INIT] Symbol '%s' not found", g_symbol);
      return INIT_FAILED;
   }
   g_sym.RefreshRates();
   g_trade.SetExpertMagicNumber(Magic_Number);
   g_trade.SetMarginMode();
   g_trade.SetTypeFillingBySymbol(g_symbol);
   g_trade.LogLevel(LOG_LEVEL_ERRORS);

   h_ema_fast = iMA(g_symbol, PERIOD_H1, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
   h_ema_slow = iMA(g_symbol, PERIOD_H1, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
   h_atr      = iATR(g_symbol, PERIOD_H1, ATR_Period);
   if (h_ema_fast==INVALID_HANDLE || h_ema_slow==INVALID_HANDLE || h_atr==INVALID_HANDLE) {
      Print("[INIT] indicator handle failed");
      return INIT_FAILED;
   }

   PrintFormat("[INIT] XAU XIM H1 strategy on %s | magic=%I64d | hours %d-%d UTC",
               g_symbol, Magic_Number, Active_Hour_Start, Active_Hour_End);
   PrintFormat("[INIT] Trend: EMA(%d-%d)/ATR > %.1f, EMA50 rising over %d bars",
               EMA_Fast, EMA_Slow, Trend_Separation_ATR, EMA_Slope_Lookback);
   PrintFormat("[INIT] Thrust: range > %.1f*ATR, body > %.0f%%, bull close",
               Thrust_Range_Mult, Thrust_Body_Ratio*100);
   PrintFormat("[INIT] Pullback: tag EMA50, body > %.0f%%", Pullback_Body_Ratio*100);
   PrintFormat("[INIT] Stop %.1f*ATR, TP %.1fR, time exit %d bars, risk %.1f%%",
               ATR_Stop_Mult, RR_Target, Max_Bars_In_Trade, Risk_Percent);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {
   IndicatorRelease(h_ema_fast);
   IndicatorRelease(h_ema_slow);
   IndicatorRelease(h_atr);
}

//==================== OnTick =====================================//
void OnTick() {
   ManageOpenPositions();
   datetime cur = iTime(g_symbol, PERIOD_H1, 0);
   if (cur == g_last_bar_time) return;
   g_last_bar_time = cur;
   ResetDailyCounterIfNewDay();
   if (CountMyOpenPositions() >= Max_Open_Positions) return;
   if (g_today_trades >= Max_Trades_Per_Day) return;
   CheckSignal();
}

//==================== Signal ====================================//
void CheckSignal() {
   // Acting on the bar that just CLOSED — index 1 on H1
   double ema_fast[3], ema_slow[3], atr[3];
   ArraySetAsSeries(ema_fast, true);
   ArraySetAsSeries(ema_slow, true);
   ArraySetAsSeries(atr, true);

   // Need fast EMA history for slope (EMA_Slope_Lookback bars back)
   double ema_fast_hist[];
   ArraySetAsSeries(ema_fast_hist, true);
   if (CopyBuffer(h_ema_fast, 0, 1, EMA_Slope_Lookback+5, ema_fast_hist) <= 0) return;
   if (CopyBuffer(h_ema_slow, 0, 1, 3, ema_slow) <= 0) return;
   if (CopyBuffer(h_atr,      0, 1, 3, atr)      <= 0) return;

   double ef_now  = ema_fast_hist[0];
   double ef_back = ema_fast_hist[EMA_Slope_Lookback];
   double es_now  = ema_slow[0];
   double atr_now = atr[0];

   // Last closed H1 bar OHLC + hour
   double op    = iOpen(g_symbol, PERIOD_H1, 1);
   double cl    = iClose(g_symbol, PERIOD_H1, 1);
   double hi    = iHigh(g_symbol, PERIOD_H1, 1);
   double lo    = iLow(g_symbol, PERIOD_H1, 1);
   datetime tt  = iTime(g_symbol, PERIOD_H1, 1);
   MqlDateTime ts; TimeToStruct(tt, ts);
   int hr = ts.hour;

   // Active hours
   if (hr < Active_Hour_Start || hr > Active_Hour_End) return;

   // Trend filter
   if (atr_now <= 0) return;
   double trend_sep = (ef_now - es_now) / atr_now;
   bool ema_rising = ef_now > ef_back;
   bool above_fast = cl > ef_now;
   bool in_uptrend = (trend_sep > Trend_Separation_ATR) && ema_rising && above_fast;
   if (!in_uptrend) return;

   // Triggers
   double bar_range = hi - lo;
   if (bar_range <= 0) return;
   double body = MathAbs(cl - op);
   bool bull = cl > op;

   // A) Momentum thrust
   bool thrust = (bar_range > Thrust_Range_Mult * atr_now) && bull && (body / bar_range > Thrust_Body_Ratio);

   // B) EMA50 pullback bounce
   bool pullback = (lo <= ef_now) && (cl > ef_now) && bull && (body / bar_range > Pullback_Body_Ratio);

   if (!thrust && !pullback) return;

   string trigger_name = thrust ? \"THRUST\" : \"PULLBACK\";

   // Compute SL/TP from CURRENT market price
   g_sym.RefreshRates();
   double entry = g_sym.Ask();
   double risk_dist = ATR_Stop_Mult * atr_now;
   double sl = entry - risk_dist;
   double tp = entry + RR_Target * risk_dist;

   // Lot size
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amt = balance * Risk_Percent / 100.0;
   double tick_value = g_sym.TickValue();
   double tick_size  = g_sym.TickSize();
   if (tick_value<=0 || tick_size<=0) return;
   double risk_per_lot = (risk_dist / tick_size) * tick_value;
   double lots = (risk_per_lot > 0) ? risk_amt / risk_per_lot : 0;
   double vol_step = g_sym.LotsStep();
   double vol_min  = g_sym.LotsMin();
   double vol_max  = g_sym.LotsMax();
   lots = MathFloor(lots / vol_step) * vol_step;
   lots = MathMax(vol_min, MathMin(vol_max, lots));
   lots = MathMax(Min_Lot, MathMin(Max_Lot, lots));

   double final_risk = (risk_dist / tick_size) * tick_value * lots;
   PrintFormat("[OPEN] BUY %s @ %.2f SL=%.2f TP=%.2f lots=%.2f risk=$%.2f bal=$%.2f trigger=%s",
               g_symbol, entry, sl, tp, lots, final_risk, balance, trigger_name);

   if (g_trade.Buy(lots, g_symbol, 0, sl, tp, Trade_Comment + \":\" + trigger_name)) {
      ulong ticket = g_trade.ResultOrder();
      RegisterPosition(ticket);
      g_today_trades++;
   } else {
      PrintFormat(\"[OPEN FAIL] retcode=%d msg=%s\",
                  g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription());
   }
}

//==================== Trade management ==========================//
void ManageOpenPositions() {
   for (int i = PositionsTotal()-1; i >= 0; i--) {
      if (!g_pos.SelectByIndex(i)) continue;
      if (g_pos.Magic() != Magic_Number) continue;
      if (g_pos.Symbol() != g_symbol) continue;
      ulong ticket = g_pos.Ticket();

      // Time exit
      int sidx = FindStateIdx(ticket);
      if (sidx >= 0) {
         int bars_held = iBarShift(g_symbol, PERIOD_H1, g_states[sidx].opened_at_bar);
         if (bars_held >= Max_Bars_In_Trade) {
            PrintFormat(\"[TIME EXIT] ticket=%I64u closed after %d bars\", ticket, bars_held);
            g_trade.PositionClose(ticket);
            continue;
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

void RegisterPosition(ulong ticket) {
   int i = ArraySize(g_states);
   ArrayResize(g_states, i+1);
   g_states[i].ticket = ticket;
   g_states[i].opened_at_bar = iTime(g_symbol, PERIOD_H1, 0);
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
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   datetime today = StringToTime(StringFormat(\"%04d.%02d.%02d 00:00\", dt.year, dt.mon, dt.day));
   if (g_today_date != today) {
      g_today_date = today;
      g_today_trades = 0;
   }
}
//+------------------------------------------------------------------+
