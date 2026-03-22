from collections import deque

# ── DEMAND FORECASTER ─────────────────────────────────────────────────

class DemandForecaster:
    def __init__(self, window=10):
        self.history    = deque(maxlen=window)
        self.window     = window
        self.prediction = 0

    def record(self, order_count: int):
        self.history.append(order_count)

    def predict_next(self) -> int:
        if len(self.history) < 2:
            return 3
        weights  = list(range(1, len(self.history) + 1))
        weighted = sum(w * v for w, v in zip(weights, self.history))
        total_w  = sum(weights)
        pred     = round(weighted / total_w)
        self.prediction = pred
        return pred

    def get_trend(self) -> str:
        if len(self.history) < 3:
            return "stable"
        recent = list(self.history)[-3:]
        if recent[-1] > recent[0] * 1.2:
            return "rising"
        elif recent[-1] < recent[0] * 0.8:
            return "falling"
        return "stable"

    def get_summary(self) -> dict:
        history_list = list(self.history)
        return {
            "history":    history_list,
            "prediction": self.predict_next(),
            "trend":      self.get_trend(),
            "avg_demand": round(sum(history_list) / max(len(history_list), 1), 1),
            "peak":       max(history_list) if history_list else 0,
            "window":     self.window
        }

# ── SINGLETON ─────────────────────────────────────────────────────────

forecaster = DemandForecaster(window=10)

def get_forecaster():
    return forecaster