import utilities
import requests
import gspread
import json
from datetime import datetime


script_id = "job_listings"



def get_listing_data():
  if utilities.use_test_data:
    sheet_data = [{'Id': 'df3434f3f', 'Timestamp': '2024-05-23T17:13:11.505Z', 'Approved': 'TRUE', 'Name': 'name', 'Position': 'title', 'Description': 'description', 'Location': 'location', 'Location Details': '', 'Type': 'Full-Time', 'Description Link': 'https://description.link', 'Application': 'application link/email', 'Compensation': '$100k-140k CAD', 'Transaction': 'https://etherscan.io', 'Contact': 'listing contact'}, {'Id': 'df3433f3f', 'Timestamp': '2024-05-23T17:13:11.505Z', 'Approved': '', 'Name': 'name', 'Position': 'title', 'Description': 'description', 'Location': 'Remote', 'Location Details': '', 'Type': 'Full-Time', 'Description Link': 'https://long.description', 'Application': 'Application Link/Email *', 'Compensation': '$100k-140k CAD', 'Transaction': 'https://etherscan.io', 'Contact': 'contact'}, {'Id': 'df3423f3f', 'Timestamp': '2024-05-23T17:13:11.505Z', 'Approved': '', 'Name': 'name', 'Position': 'title', 'Description': 'description', 'Location': 'Remote', 'Location Details': '', 'Type': 'Full-Time', 'Description Link': 'https://long.description', 'Application': 'link/email', 'Compensation': '$100k-140k CAD', 'Transaction': 'https://etherscan.io', 'Contact': 'contact'}, {'Id': 'df343f93f', 'Timestamp': '2024-05-23T17:13:11.505Z', 'Approved': '', 'Name': 'fgdfg', 'Position': 'fgdfg', 'Description': 'sfgfsg', 'Location': 'Remote', 'Location Details': 'Location Details', 'Type': 'Full-Time', 'Description Link': 'https://docs.google.com/', 'Application': 'https://docs.google.com/', 'Compensation': '$100k-140k CAD', 'Transaction': 'https://docs.google.com/', 'Contact': 'contatd'}, {'Id': 'df3435f3f', 'Timestamp': '2024-05-23T17:13:11.505Z', 'Approved': '', 'Name': 'name', 'Position': 'title', 'Description': 'Role Description (300 characters m', 'Location': 'Onsite', 'Location Details': 'onsite city, country', 'Type': 'Contract', 'Description Link': 'https://long.description', 'Application': 'link/email', 'Compensation': '$100k-140k CAD', 'Transaction': 'https://etherscan.io', 'Contact': 'contact'}]
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
  current_listings = utilities.read_file(f"_data/job-listings.json")
  approved_listings = []
  new_listing_submissions = []
  newly_approved_listings = []
  newly_expired_listings = []

  # reformat and create lists of approved and new listings
  for row in raw_data:
    entry = {
      "id": row["Id"],
      "epoch": utilities.current_time,
      "name": row["Name"],
      "position": row["Position"],
      "description": row["Description"],
      "comp": row["Compensation"],
      "location": row["Location"],
      "location_details": row["Location Details"],
      "type": row["Type"],
      "description_link": row["Description Link"],
      "apply": row["Application"]
    }
    if row["Approved"] == "TRUE":
      approved_listings.append(entry)
    elif row["Approved"] == "":
      new_listing_submissions.append(entry)

  # create list of newly expired listings
  for listing in current_listings:
    # expired if more than 31 days old (one day grace period to account for script delay)
    expired = (utilities.current_time - listing["epoch"]) > 2592000
    if expired:
      newly_expired_listings.append(listing)

  # create list of newly approved listings
  # set epoch time if approved listing is a current listing
  for approved_listing in approved_listings:
    is_new_listing = True
    for current_listing in current_listings:
      if approved_listing["id"] == current_listing["id"]:
        is_new_listing = False
        approved_listing["epoch"] = current_listing["epoch"]
    if is_new_listing:
      newly_approved_listings.append(approved_listing)

  # send discord ping for new listings
  for listing in newly_approved_listings:
    position = f"**{listing['position'].strip().title()}**"
    name = f"*{listing['name'].strip()}*"
    role_type = f"{listing['type'].strip()}"
    location_type = f"{listing['location'].strip()}"
    comp = f"{listing['comp'].strip()}"
    location = ""
    if listing["location"] != "Remote":
      location = f"Location: {listing['location_details'].strip().lower()}\n"
    description = ""
    if listing["description"]:
      description = f"> {listing['description'].strip()}\n\n"
    description += f"[Full listing description](<{listing['description_link']}>)\n"
    application = f"[Apply](<{listing['apply']}>)"
    if "[at]" in listing["apply"]:
      application = f"Email to apply: {listing['apply'].strip()}"
    msg = "\n".join((
      f"{position}  ({name})",
      f"{role_type}  |  {location_type}  |  {comp}",
      f"{location}",
      f"{description}",
      f"{application}",
      f"\n---------------------------------"))
    utilities.sendDiscordMsg(utilities.DISCORD_JOB_LISTINGS_WEBHOOK, msg)

  # send discord ping for new listing submissions
  if len(new_listing_submissions) > 0:
    plural = ""
    if len(new_listing_submissions) > 1:
      plural = "s"
    msg = f"[{len(new_listing_submissions)} new job listing{plural}](<{utilities.JOB_LISTINGS_URL}>)"
    utilities.sendDiscordMsg(utilities.DISCORD_WEBSITE_WEBHOOK, msg)

  # send discord ping for expired listings
  if len(newly_expired_listings) > 0:
    plural = ""
    ids = []
    if len(newly_expired_listings) > 1:
      plural = "s"
    for listing in newly_expired_listings:
      ids.append(listing["id"])
    msg = f"[{len(newly_expired_listings)} expired job listing{plural}](<{utilities.JOB_LISTINGS_URL}>): {', '.join(ids)}"
    # utilities.sendDiscordMsg(utilities.DISCORD_WEBSITE_WEBHOOK, msg)
  utilities.log(approved_listings, context=f"{script_id}__process_listing_data")
  return approved_listings

def save_listing_data(approved_listings):
  utilities.save_to_file(f"_data/job-listings.json", approved_listings, context=f"{script_id}__save_listing_data")


def update_job_listings():
  try:
    raw_data = get_listing_data()
    approved_listings = process_listing_data(raw_data)
    save_listing_data(approved_listings)
  except Exception as error:
    utilities.log(f"{error}: {script_id}")
    utilities.report_error(error, context=f"{script_id}__update_job_listings")


