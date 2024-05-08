import utilities
from smoothing_pools import update_smoothing_pool_data
from hardware import check_hardware_availability



def run_app():
  update_smoothing_pool_data()
  check_hardware_availability()


run_app()
print(f"Error count: {utilities.error_count}")

