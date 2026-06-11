//+------------------------------------------------------------------+
//|                                          XAU_Strategy_Tester.mq5 |
//|  Backtest the ACTUAL 50 EMA Williams strategy in MT5's tester.    |
//|                                                                    |
//|  Mirrors backtest/strategies/ema_williams.py exactly:              |
//|   LONG  = Close > 50 EMA-High channel AND                          |
//|           Williams %R crosses up through -20 AND                   |
//|           Stoch %K > %D AND %K > 60 AND                            |
//|           Close > EMA200 (trend filter)                            |
//|   SHORT = mirror                                                   |
//|   Stop  = recent swing(10) extreme +/- 0.5 * ATR(14)               |
//|   Target= fixed 2R                                                 |
//|   Time  = exit after 50 bars if neither hit                        |
//|                                                                    |
//|  Then layers your existing trade management:                       |
//|   BE at +1R, partial 50% at +1.5R, trail after partial by ATR.     |
//+------------------------------------------------------------------+
#property copyright "trading_setup"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/SymbolInfo.mqh>

//==================== Inputs ====================================//
input group "Strategy rules (50 EMA Williams)"
input ENUM_TIMEFRAMES Strategy_TF        = PERIOD_D1;   // D1 = best risk-adj per backtest (54.8% WR, 1.82 PF, -4.3% DD)
input int     Channel_Period             = 50;
input int     Trend_EMA                  = 200;
input int     WR_Period                  = 14;
input double  WR_Long_Threshold          = -20;
input double  WR_Short_Threshold         = -80;
input int     Stoch_K                    = 14;
input int     Stoch_D                    = 3;
input int     Stoch_Smooth               = 3;
input double  Stoch_Long_Threshold       = 60;
input double  Stoch_Short_Threshold      = 40;
input int     Swing_Lookback             = 10;
input int     ATR_Period                 = 14;
input double  ATR_Stop_Buffer            = 0.5;
input double  RR_Target                  = 2.0;
input int     Max_Bars_In_Trade          = 50;

input group "Risk"
input double  Risk_Percent               = 1.0;
input double  Min_Lot                    = 0.01;
input double  Max_Lot                    = 1.00;
input int     Max_Open_Positions         = 1;

input group "Trade Management (bot's rules)"
input bool    Use_BE                     = true;
input double  BE_Trigger_R               = 1.0;
input double  BE_Buffer_Points           = 2.0;
input bool    Use_Partial_Close          = true;
input double  Partial_R                  = 1.5;
input double  Partial_Percent            = 50.0;
input bool    Use_Trailing               = true;
input double  Trail_ATR_Mult             = 0.5;
input bool    Use_Time_Exit              = true;

input group "Identity"
input long    Magic_Number               = 4040407;
input string  Trade_Comment              = "xau-strat";

//==================== Globals ===================================//
CTrade         g_trade;
CPositionInfo  g_pos;
CSymbolInfo    g_sym;

string         g_symbol;
int            h_ema_high      = INVALID_HANDLE;
int            h_ema_low       = INVALID_HANDLE;
int            h_ema_trend     = INVALID_HANDLE;
int            h_wr            = INVALID_HANDLE;
int            h_stoch         = INVALID_HANDLE;
int            h_atr           = INVALID_HANDLE;
datetime       g_last_bar_time = 0;

struct PosState {
   ulong   ticket;
   bool    be_done;
   bool    partial_done;
   double  original_sl;
   double  original_risk;
   double  original_entry;
   datetime opened_at_bar;
};
PosState g_states[];

//==================== OnInit ====================================//
int OnInit() {
   g_symbol = _Symbol;
   if (!g_sym.Name(g_symbol)) {
      PrintFormat("[INIT] Symbol '%s' not found.", g_symbol);
      return INIT_FAILED;
   }
   g_sym.RefreshRates();
   g_trade.SetExpertMagicNumber(Magic_Number);
   g_trade.SetMarginMode();
   g_trade.SetTypeFillingBySymbol(g_symbol);
   g_trade.LogLevel(LOG_LEVEL_ERRORS);

   // Indicator handles on strategy TF
   h_ema_high  = iMA(g_symbol, Strategy_TF, Channel_Period, 0, MODE_EMA, PRICE_HIGH);
   h_ema_low   = iMA(g_symbol, Strategy_TF, Channel_Period, 0, MODE_EMA, PRICE_LOW);
   h_ema_trend = iMA(g_symbol, Strategy_TF, Trend_EMA,      0, MODE_EMA, PRICE_CLOSE);
   h_wr        = iWPR(g_symbol, Strategy_TF, WR_Period);
   h_stoch     = iStochastic(g_symbol, Strategy_TF, Stoch_K, Stoch_D, Stoch_Smooth, MODE_SMA, STO_LOWHIGH);
   h_atr       = iATR(g_symbol, Strategy_TF, ATR_Period);

   if (h_ema_high == INVALID_HANDLE || h_ema_low == INVALID_HANDLE || h_ema_trend == INVALID_HANDLE
       || h_wr == INVALID_HANDLE || h_stoch == INVALID_HANDLE || h_atr == INVALID_HANDLE) {
      Print("[INIT] indicator handle failed");
      return INIT_FAILED;
   }

   PrintFormat("[INIT] 50 EMA Williams strategy on %s TF=%s, magic=%I64d",
               g_symbol, EnumToString(Strategy_TF), Magic_Number);
   PrintFormat("[INIT] Rules: ch=%d, trend=%d, WR(%d)>%.0f/<%.0f, Stoch>%.0f/<%.0f, swing=%d, ATR buf=%.1f, TP=%.1fR",
               Channel_Period, Trend_EMA, WR_Period, WR_Long_Threshold, WR_Short_Threshold,
               Stoch_Long_Threshold, Stoch_Short_Threshold, Swing_Lookback, ATR_Stop_Buffer, RR_Target);
   PrintFormat("[INIT] Mgmt: BE@+%.1fR | Partial %.0f%%@+%.1fR | Trail %.1fxATR | Time exit %d bars",
               BE_Trigger_R, Partial_Percent, Partial_R, Trail_ATR_Mult, Max_Bars_In_Trade);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {
   IndicatorRelease(h_ema_high);
   IndicatorRelease(h_ema_low);
   IndicatorRelease(h_ema_trend);
   IndicatorRelease(h_wr);
   IndicatorRelease(h_stoch);
   IndicatorRelease(h_atr);
}

//==================== Tick =====================================//
void OnTick() {
   // Manage every tick
   ManageOpenPositions();

   // Check for new signal only on new bar close (no look-ahead)
   datetime current_bar = iTime(g_symbol, Strategy_TF, 0);
   if (current_bar == g_last_bar_time) return;
   g_last_bar_time = current_bar;

   // Don't take new trade if we already have one
   if (CountMyOpenPositions() >= Max_Open_Positions) return;

   CheckSignal();
}

//==================== Signal check =============================//
void CheckSignal() {
   // We work on the LAST CLOSED bar (index 1), entry on next bar's open (index 0 / market)
   // Need at least 2 bars of history (current + previous) for "cross" detection.
   double ema_high[2], ema_low[2], ema_trend[2];
   double wr[2], stk[2], std[2], atr[2];
   double close[2], high_arr[1+Swing_Lookback], low_arr[1+Swing_Lookback];

   ArraySetAsSeries(ema_high, true);
   ArraySetAsSeries(ema_low, true);
   ArraySetAsSeries(ema_trend, true);
   ArraySetAsSeries(wr, true);
   ArraySetAsSeries(stk, true);
   ArraySetAsSeries(std, true);
   ArraySetAsSeries(atr, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(high_arr, true);
   ArraySetAsSeries(low_arr, true);

   if (CopyBuffer(h_ema_high,  0, 1, 2, ema_high)  <= 0) return;
   if (CopyBuffer(h_ema_low,   0, 1, 2, ema_low)   <= 0) return;
   if (CopyBuffer(h_ema_trend, 0, 1, 2, ema_trend) <= 0) return;
   if (CopyBuffer(h_wr,        0, 1, 2, wr)        <= 0) return;
   if (CopyBuffer(h_stoch,     0, 1, 2, stk)       <= 0) return;
   if (CopyBuffer(h_stoch,     1, 1, 2, std)       <= 0) return;
   if (CopyBuffer(h_atr,       0, 1, 2, atr)       <= 0) return;
   if (CopyClose(g_symbol, Strategy_TF, 1, 2, close) <= 0) return;
   if (CopyHigh(g_symbol, Strategy_TF, 1, Swing_Lookback, high_arr) <= 0) return;
   if (CopyLow(g_symbol, Strategy_TF,  1, Swing_Lookback, low_arr)  <= 0) return;

   // Last closed bar values (index 0 of "as series" arrays)
   double c        = close[0];
   double c_prev   = close[1];
   double eh       = ema_high[0];
   double el       = ema_low[0];
   double et       = ema_trend[0];
   double wr_now   = wr[0];
   double wr_prev  = wr[1];
   double stk_now  = stk[0];
   double std_now  = std[0];
   double atr_val  = atr[0];

   // Swing extremes over last N bars (excluding current = already-closed)
   double swing_high = high_arr[ArrayMaximum(high_arr)];
   double swing_low  = low_arr[ArrayMinimum(low_arr)];

   // Cross detection
   bool wr_cross_up   = (wr_now > WR_Long_Threshold)  && (wr_prev <= WR_Long_Threshold);
   bool wr_cross_down = (wr_now < WR_Short_Threshold) && (wr_prev >= WR_Short_Threshold);

   bool long_sig =
      (c > eh) &&
      wr_cross_up &&
      (stk_now > std_now) && (stk_now > Stoch_Long_Threshold) &&
      (c > et);

   bool short_sig =
      (c < el) &&
      wr_cross_down &&
      (stk_now < std_now) && (stk_now < Stoch_Short_Threshold) &&
      (c < et);

   if (!long_sig && !short_sig) return;

   // Entry at current bar's open (next bar after close) — i.e. current market price
   g_sym.RefreshRates();
   double entry_now = long_sig ? g_sym.Ask() : g_sym.Bid();
   double sl, tp;
   if (long_sig) {
      sl = swing_low - ATR_Stop_Buffer * atr_val;
      double r = entry_now - sl;
      if (r <= 0) return;
      tp = entry_now + RR_Target * r;
      OpenTrade("BUY", entry_now, sl, tp, r);
   } else {
      sl = swing_high + ATR_Stop_Buffer * atr_val;
      double r = sl - entry_now;
      if (r <= 0) return;
      tp = entry_now - RR_Target * r;
      OpenTrade("SELL", entry_now, sl, tp, r);
   }
}

//==================== Open trade ===============================//
void OpenTrade(string direction, double entry, double sl, double tp, double risk_dist) {
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amt = balance * Risk_Percent / 100.0;
   double tick_value = g_sym.TickValue();
   double tick_size  = g_sym.TickSize();
   if (tick_value <= 0 || tick_size <= 0) return;

   double risk_per_lot = (risk_dist / tick_size) * tick_value;
   double lots = (risk_per_lot > 0) ? risk_amt / risk_per_lot : 0;

   double vol_step = g_sym.LotsStep();
   double vol_min  = g_sym.LotsMin();
   double vol_max  = g_sym.LotsMax();
   lots = MathFloor(lots / vol_step) * vol_step;
   lots = MathMax(vol_min, MathMin(vol_max, lots));
   lots = MathMax(Min_Lot, MathMin(Max_Lot, lots));

   double final_risk = (risk_dist / tick_size) * tick_value * lots;
   PrintFormat("[OPEN] %s %s @ %.2f SL=%.2f TP=%.2f lots=%.2f risk=$%.2f bal=$%.2f",
               direction, g_symbol, entry, sl, tp, lots, final_risk, balance);

   bool ok = (direction == "BUY")
      ? g_trade.Buy(lots, g_symbol, 0, sl, tp, Trade_Comment)
      : g_trade.Sell(lots, g_symbol, 0, sl, tp, Trade_Comment);
   if (!ok) {
      PrintFormat("[OPEN FAIL] retcode=%d msg=%s",
                  g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription());
      return;
   }
   ulong ticket = g_trade.ResultOrder();
   RegisterPosition(ticket, entry, sl, risk_dist);
}

//==================== Trade management =========================//
void ManageOpenPositions() {
   for (int i = PositionsTotal() - 1; i >= 0; i--) {
      if (!g_pos.SelectByIndex(i)) continue;
      if (g_pos.Magic() != Magic_Number) continue;
      if (g_pos.Symbol() != g_symbol) continue;

      ulong ticket = g_pos.Ticket();
      int sidx = FindStateIdx(ticket);
      if (sidx < 0) {
         RegisterPosition(ticket, g_pos.PriceOpen(), g_pos.StopLoss(),
                          MathAbs(g_pos.PriceOpen() - g_pos.StopLoss()));
         sidx = FindStateIdx(ticket);
         if (sidx < 0) continue;
      }

      // Time exit
      if (Use_Time_Exit && Max_Bars_In_Trade > 0) {
         datetime current_bar = iTime(g_symbol, Strategy_TF, 0);
         int bars_held = iBarShift(g_symbol, Strategy_TF, g_states[sidx].opened_at_bar);
         if (bars_held >= Max_Bars_In_Trade) {
            PrintFormat("[TIME EXIT] ticket=%I64u closed after %d bars", ticket, bars_held);
            g_trade.PositionClose(ticket);
            continue;
         }
      }

      double entry      = g_states[sidx].original_entry;
      double orig_risk  = g_states[sidx].original_risk;
      bool   is_buy     = (g_pos.PositionType() == POSITION_TYPE_BUY);

      g_sym.RefreshRates();
      double price = is_buy ? g_sym.Bid() : g_sym.Ask();
      double favorable = is_buy ? (price - entry) : (entry - price);
      double r_multiple = (orig_risk > 0) ? favorable / orig_risk : 0;

      // BE
      if (Use_BE && !g_states[sidx].be_done && r_multiple >= BE_Trigger_R) {
         double buf = BE_Buffer_Points * g_sym.Point();
         double new_sl = is_buy ? entry + buf : entry - buf;
         if (g_trade.PositionModify(ticket, new_sl, g_pos.TakeProfit())) {
            g_states[sidx].be_done = true;
            PrintFormat("[BE] ticket=%I64u SL->BE %.2f at +%.2fR", ticket, new_sl, r_multiple);
         }
      }

      // Partial
      if (Use_Partial_Close && !g_states[sidx].partial_done && r_multiple >= Partial_R) {
         double close_vol = NormalizeVolume(g_pos.Volume() * (Partial_Percent / 100.0));
         if (close_vol >= g_sym.LotsMin() && close_vol < g_pos.Volume()) {
            if (g_trade.PositionClosePartial(ticket, close_vol)) {
               g_states[sidx].partial_done = true;
               PrintFormat("[PARTIAL] ticket=%I64u closed %.2f at +%.2fR", ticket, close_vol, r_multiple);
            }
         }
      }

      // Trail
      if (Use_Trailing && g_states[sidx].partial_done) {
         double atr_buf[1];
         ArraySetAsSeries(atr_buf, true);
         if (CopyBuffer(h_atr, 0, 0, 1, atr_buf) > 0) {
            double trail_dist = atr_buf[0] * Trail_ATR_Mult;
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

void RegisterPosition(ulong ticket, double entry, double sl, double risk) {
   int i = ArraySize(g_states);
   ArrayResize(g_states, i + 1);
   g_states[i].ticket = ticket;
   g_states[i].be_done = false;
   g_states[i].partial_done = false;
   g_states[i].original_sl = sl;
   g_states[i].original_risk = (risk > 0) ? risk : MathAbs(entry - sl);
   g_states[i].original_entry = entry;
   g_states[i].opened_at_bar = iTime(g_symbol, Strategy_TF, 0);
}

int CountMyOpenPositions() {
   int count = 0;
   for (int i = 0; i < PositionsTotal(); i++) {
      if (!g_pos.SelectByIndex(i)) continue;
      if (g_pos.Magic() == Magic_Number && g_pos.Symbol() == g_symbol) count++;
   }
   return count;
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
