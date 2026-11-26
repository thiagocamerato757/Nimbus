from hypothesis import settings

settings.register_profile("nimbus", derandomize=True, database=None, max_examples=80)
settings.load_profile("nimbus")
