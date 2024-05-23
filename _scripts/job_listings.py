import utilities
import requests
import gspread
import json
from datetime import datetime


script_id = "job_listings"



def get_listing_data():
  if utilities.use_test_data:
    sheet_data = [{'Id': 'df3434f3f', 'Timestamp': '2024-05-23T17:13:11.505Z', 'Approved': 'TRUE', 'Name': 'name', 'Position': 'title', 'Description': 'description', 'Location': 'location', 'Location Details': '', 'Type': 'Full-Time', 'Description Link': 'https://description.link', 'Application': 'application link/email', 'Transaction': 'https://etherscan.io', 'Contact': 'listing contact'}, {'Id': 'df3433f3f', 'Timestamp': '2024-05-23T17:13:11.505Z', 'Approved': '', 'Name': 'name', 'Position': 'title', 'Description': 'description', 'Location': 'Remote', 'Location Details': '', 'Type': 'Full-Time', 'Description Link': 'https://long.description', 'Application': 'Application Link/Email *', 'Transaction': 'https://etherscan.io', 'Contact': 'contact'}, {'Id': 'df3423f3f', 'Timestamp': '2024-05-23T17:13:11.505Z', 'Approved': '', 'Name': 'name', 'Position': 'title', 'Description': 'description', 'Location': 'Remote', 'Location Details': '', 'Type': 'Full-Time', 'Description Link': 'https://long.description', 'Application': 'link/email', 'Transaction': 'https://etherscan.io', 'Contact': 'contact'}, {'Id': 'df343f93f', 'Timestamp': '2024-05-23T17:13:11.505Z', 'Approved': '', 'Name': 'fgdfg', 'Position': 'fgdfg', 'Description': 'sfgfsg', 'Location': 'Remote', 'Location Details': 'Location Details', 'Type': 'Full-Time', 'Description Link': 'https://docs.google.com/', 'Application': 'https://docs.google.com/', 'Transaction': 'https://docs.google.com/', 'Contact': 'contatd'}, {'Id': 'df3435f3f', 'Timestamp': '2024-05-23T17:13:11.505Z', 'Approved': '', 'Name': 'name', 'Position': 'title', 'Description': 'Role Description (300 characters m', 'Location': 'Onsite', 'Location Details': 'onsite city, country', 'Type': 'Contract', 'Description Link': 'https://long.description', 'Application': 'link/email', 'Transaction': 'https://etherscan.io', 'Contact': 'contact'}]
  else:
    credentials = utilities.GOOGLE_CREDENTIALS
    # get the sheet data
    # reference: https://docs.gspread.org/en/v5.7.0/user-guide.html
    gc = gspread.service_account_from_dict(credentials)
    sheet = gc.open_by_key(utilities.SHEETS_URL).worksheet("Job Listings")
    sheet_data = sheet.get_all_records()
  # utilities.log(sheet_data, context=f"{script_id}__get_listing_data")
  return sheet_data

def process_listing_data(raw_data):
  processed_data = []
  current_listings = utilities.read_file(f"_data/job-listings.json")
  approved_listings = []
  new_listings = 0
  # filter for approved listings and reformat
  for row in raw_data:
    if row["Approved"] == "TRUE":
      entry = {
        "id": row["Id"],
        "epoch": utilities.current_time,
        "name": row["Name"],
        "position": row["Position"],
        "description": row["Description"],
        "location": row["Location"],
        "location_details": row["Location Details"],
        "type": row["Type"],
        "description_link": row["Description Link"],
        "apply": row["Application"]
      }
      approved_listings.append(entry)
    elif row["Approved"] == "":
      new_listings += 1
  # filter for newly approved listings
  for approved_listing in approved_listings:
    is_new_listing = True
    for listing in current_listings:
      if approved_listing["id"] == listing["id"]:
        is_new_listing = False
    if is_new_listing:
      processed_data.append(approved_listing)
  # filter expired listings from current_listings
  for listing in current_listings:
    # active if less than 31 days old
    active = (utilities.current_time - listing["epoch"]) < 2592000
    if active:
      processed_data.append(listing)
  # send discord ping for new listings
  if new_listings > 0:
    plural = ""
    if new_listings > 1:
      plural = "s"
    msg = f"[{new_listings} new job listing{plural}](<{utilities.JOB_LISTINGS_URL}>)"
    utilities.sendDiscordMsg(msg)
  utilities.log(processed_data, context=f"{script_id}__process_listing_data")
  return processed_data

def save_listing_data(processed_data):
  utilities.save_to_file(f"_data/job-listings.json", processed_data, context=f"{script_id}__save_listing_data")


def update_job_listings():
  try:
    raw_data = get_listing_data()
    processed_data = process_listing_data(raw_data)
    save_listing_data(processed_data)
  except Exception as error:
    utilities.log(f"{error}: {script_id}")
    utilities.report_error(error, context=f"{script_id}__update_job_listings")


