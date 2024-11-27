import utilities
import requests
import gspread
import json
from dateutil import parser


script_id = "job_listings"



def get_listing_data():
  if utilities.use_test_data:
    sheet_data = [{'Approved': 'TRUE', 'Timestamp': '7/17/2024 15:15:24', 'Id': '0e1415b4487f694df10ba670ef13368e1', 'Name': 'Protocol Guild', 'Position': 'Generalist', 'Description': 'Protocol Guild is a collective funding mechanism for +180 Ethereum core protocol contributors: seeking another generalist to help operate the mechanism & fundraise ⭐️ membership includes access to the current ~$50mm, + any future inflows \U0001fae1 come work on the bleeding edge of OSS/commons funding', 'Location': 'Remote', 'Location Details': '', 'Type': 'Full-Time', 'Compensation': 'min ~89k, commission', 'Description Link': 'https://cryptpad.fr/pad/#/2/pad/view/O0CguV6OBAKa8zRYtdBQXy6wBNuEet4111hVU3Y3qR8/', 'Application': 'https://discord.gg/uc5ZgXS5mQ', 'Transaction': 'x.com/trent_vanepps', 'Contact': 'trent'}, {'Approved': 'TRUE', 'Timestamp': '10/15/2024 23:17:25', 'Id': '0e1415b4487f694df10ba670ef13368e2', 'Name': 'Ethereum Foundation', 'Position': 'Protocol Tester', 'Description': "We’re seeking passionate and collaborative individuals who are excited about testing Ethereum to help reduce the risk of software failures across the protocol. You'll collaborate with other testers, dev operatooors, client developers, and protocol researchers to ensure protocol upgrades are....", 'Location': 'Remote', 'Location Details': '', 'Type': 'Full-Time', 'Compensation': 'Salary TBD', 'Description Link': 'https://jobs.lever.co/ethereumfoundation/c9ef74e7-1fb7-4a8e-88cc-11aa178d49e2', 'Application': 'https://jobs.lever.co/ethereumfoundation/c9ef74e7-1fb7-4a8e-88cc-11aa178d49e2', 'Transaction': 'https://etherscan.io', 'Contact': 'hanniabu'}, {'Approved': 'TRUE', 'Timestamp': '10/31/2024 5:24:24', 'Id': '0e1415b4487f694df10ba670ef13368e3', 'Name': 'beaconcha.in', 'Position': 'Senior UI/UX Designer', 'Description': 'End-to-End Design Ownership \nLead the design process from concept to final delivery, ensuring seamless integration of user experience across all stages.\n\nDesign Structures and Components\nCreate, maintain, and enhance scalable design systems, ensuring consistency across the platform.', 'Location': 'Remote', 'Location Details': '', 'Type': 'Full-Time', 'Compensation': '€60,000', 'Description Link': '', 'Application': 'butta[at]bitfly[dot]at', 'Transaction': 'https://etherscan.io/tx/0xddbafc25e0f4544add397243b6bffb20823d56aceda56d22c3301ab259605378', 'Contact': '@butta_eth'}, {'Approved': 'TRUE', 'Timestamp': '11/25/2024 14:14:51', 'Id': '0e1415b4487f694df10ba670ef13368e4', 'Name': 'Firstset', 'Position': 'Infrastructure Lead', 'Description': 'We are seeking an experienced DevOps / SRE to become our “master of nodes” to help us grow our validator operation. Your primary responsibility will be to deploy, manage and monitor our validator nodes across various blockchain networks, ensuring they are secure, reliable, and resilient.', 'Location': 'Remote', 'Location Details': '', 'Type': 'Full-Time', 'Compensation': '80-120k EUR', 'Description Link': 'https://www.firstset.xyz/careers/infrastructure-lead', 'Application': 'careers[at]firstset[dot]xyz', 'Transaction': 'https://etherscan.io/tx/0xf40fc612c9d3ac3076e95515fde382bb72bd4356b1c97b7cc3ed0793491f8161', 'Contact': 'bernat@firstset.xyz'}]
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
  # utilities.log(len(current_listings), context=f"{script_id}__current_listings_count")
  approved_listings = []
  new_listing_submissions = []
  newly_approved_listings = []
  newly_expired_listings = []
  updated_listings = []

  # reformat and create lists of approved and new listings
  for row in raw_data:
    entry = {
      "id": row["Id"],
      "epoch": round(parser.parse(row["Timestamp"]).timestamp()),
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
    # utilities.log(entry, context=f"{script_id}__raw_data_entry")
    if row["Approved"] == "TRUE":
      approved_listings.append(entry)
      # utilities.log(row["Approved"] == "TRUE", context=f"{script_id}__is_approved_listing")
    elif row["Approved"] == "":
      new_listing_submissions.append(entry)
  # utilities.log(len(current_listings), context=f"{script_id}__current_listings_count")
  # utilities.log(len(approved_listings), context=f"{script_id}__approved_listings_count")
  # utilities.log(len(new_listing_submissions), context=f"{script_id}__new_listing_submissions_count")
  # utilities.log(len(raw_data), context=f"{script_id}__raw_data_entries_count")
  # utilities.log(new_listing_submissions, context=f"{script_id}__new_listing_submissions")

  # create list of newly approved listings
  # set epoch time if approved listing is a current listing
  for approved_listing in approved_listings:
    is_new_listing = True
    for current_listing in current_listings:
      if approved_listing["id"] == current_listing["id"]:
        is_new_listing = False
    if is_new_listing:
      approved_listing["epoch"] = utilities.current_time
      newly_approved_listings.append(approved_listing)
      updated_listings.append(approved_listing)
      # utilities.log(approved_listing, context=f"{script_id}__newly_approved_listing")
  # utilities.log(len(newly_approved_listings), context=f"{script_id}__newly_approved_listings_count")

  # create list of newly expired listings
  for listing in current_listings:
    # expired if more than 31 days old (one day grace period to account for script delay)
    expired = (utilities.current_time - listing["epoch"]) > 2592000
    if expired:
      newly_expired_listings.append(listing)
      # utilities.log(listing, context=f"{script_id}__newly_expired_listing")
    else:
      updated_listings.append(listing)
  # utilities.log(len(newly_expired_listings), context=f"{script_id}__newly_expired_listings_count")

  # post new listing to discord job listing channel
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
      description_text = listing['description'].strip().replace('\n','\n> ')
      description = f"> {description_text}\n\n"
    if listing["description_link"]:
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
  utilities.log(updated_listings, context=f"{script_id}__process_listing_data")
  return updated_listings

def save_listing_data(updated_listings):
  utilities.save_to_file(f"_data/job-listings.json", updated_listings, context=f"{script_id}__save_listing_data")


def update_job_listings():
  try:
    raw_data = get_listing_data()
    updated_listings = process_listing_data(raw_data)
    save_listing_data(updated_listings)
  except Exception as error:
    utilities.log(f"{error}: {script_id}")
    utilities.report_error(error, context=f"{script_id}__update_job_listings")
