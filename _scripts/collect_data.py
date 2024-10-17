import utilities
from smoothing_pools import update_smoothing_pool_data
from hardware import check_hardware_availability
from blog_feed import update_blog_feed
from job_listings import update_job_listings
from for_hire_listings import update_for_hire_listings



def run_app():
  update_smoothing_pool_data()
  check_hardware_availability()
  update_blog_feed()
  update_job_listings()
  update_for_hire_listings()



run_app()
print(f"Error count: {utilities.error_count}")

