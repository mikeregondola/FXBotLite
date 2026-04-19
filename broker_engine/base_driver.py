class BaseBrokerDriver:

    def execute_trade(self, signal):
        raise NotImplementedError()

    def health(self):
        return True