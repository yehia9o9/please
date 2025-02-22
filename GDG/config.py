import os

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCo_o56CNTksGuC9pyyk3EogIQG5X1jgvE")
    WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID", "E7P9HP-R9P7HKJ6PJ")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
    DEEPSEEK_MODEL_ID = os.getenv("DEEPSEEK_MODEL_ID", "deepseek/deepseek-chat:free")
    STACK_EXCHANGE_API_KEY = os.getenv("STACK_EXCHANGE_API_KEY", "rl_AkMa815x96XM6UqeAPZXWt3T3")