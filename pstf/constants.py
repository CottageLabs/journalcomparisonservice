import os
from django.utils.translation import gettext as _
from django.conf import settings

# Constants
ADMIN_EMAIL = "sysadmin@cottagelabs.com"
COALITIONS_CONTACT_EMAIL = "info@coalition-s.org"
OTP_TYPE_SMS = "sms"
OTP_TYPE_DEVICE = "device"

# Groups
COALITION_S_GROUP = "CoalitionS"
SUPER_PUBLISHER_GROUP = "SuperPublisher"
PUBLISHER_GROUP = "Publisher"
INSTITUTIONAL_SUPER_USER_GROUP = "InstitutionalSuperUser"
INSTITUTIONAL_USER_GROUP = "InstitutionalUser"

ALL_GROUPS = [COALITION_S_GROUP, SUPER_PUBLISHER_GROUP, PUBLISHER_GROUP, INSTITUTIONAL_SUPER_USER_GROUP,
              INSTITUTIONAL_USER_GROUP]

# URL Redirect
LOGIN_URL = "pstf-login"
EMAIL_OTP_URL = "email-otp"
VERIFY_OTP_URL = "verify-otp"
VERIFY_2ND_OTP_URL = "verify-2nd-otp"

#  Dashboard
SP_DASHBOARD = "s_publisher_dashboard"
PUBLISHER_DASHBOARD = "publisher_dashboard"
SPUBLISHER_USERS_DASHBOARD = "s_publisher_users"
SINSTITUTIONAL_USERS_DASHBOARD = "ins_s_users"
INS_SUPER_USER_DASHBOARD = "ins_s_user_dashboard"
INS_USER_DASHBOARD = "ins_user_dashboard"
COALITION_S_DASHBOARD = "coalitions_account_search"
COALITION_S_ACCOUNT_SEARCH = "coalitions_account_search"
COALITION_S_APPROVED_USERS = "/dashboard/coalitions/approvedusers/"
COALITION_S_AWAITING_USERS = "/dashboard/coalitions/awaitingusers/"
COALITION_S_CONTRACT_SIGNING_USERS = "/dashboard/coalitions/awaiting_contract_signing_users/"
COALITION_S_ARCHIVED_USERS = "/dashboard/coalitions/archived_user/"
COALITION_S_APPROVED_INS_USERS = "/dashboard/coalitions/approved_ins_users/"
COALITION_S_AWAITING_INS_USERS = "/dashboard/coalitions/awaiting_ins_users/"
COALITION_S_CONTRACT_SIGNING_INS_USERS = "/dashboard/coalitions/awaiting_contract_signing_ins_users/"
COALITION_S_ARCHIVED_INS_USERS = "/dashboard/coalitions/archived_ins_users/"
SPUBLISHER_APPROVED_USERS = "/dashboard/superpublisher/approvedusers/"
SPUBLISHER_AWAITING_USERS = "/dashboard/superpublisher/awaitingusers/"
SPUBLISHER_ARCHIVED_USERS = "/dashboard/superpublisher/archived_user/"
S_INS_APPROVED_USERS = "/dashboard/s_ins/approvedusers/"
S_INS_AWAITING_USERS = "/dashboard/s_ins/awaitingusers/"
S_INS_ARCHIVED_USERS = "/dashboard/s_ins/archived_user/"
SP_VERIFICATION_WORKFLOW = "/workflow/registration/publisherverification/start/"

# URL template
LOGIN_TEMPLATE = "login/login.html"
PUBLISHER_USERS_TEMPLATE = "super_publisher/users.html"
PUBLISHER_GENERATE_LINK_TEMPLATE = "super_publisher/generate.html"
INS_GENERATE_LINK_TEMPLATE = "ins_super_user/generate.html"
COALITIONS_USERS_TEMPLATE = "coalitions/dashboard.html"
INS_USERS_TEMPLATE = "ins_super_user/users.html"

# Path constants
REGISTER = "register"
EXPORT_DOWNLOAD = "dashboard/download/"
EXPORT_DIR_PATH = os.path.join(settings.BASE_DIR, "docs", "export")
TEMP_DIR = os.path.join(settings.BASE_DIR, "tmp")


# -----------------------------------------------
# Constants for upload module


all_disciplines = ['all disciplines', 'all STEM disciplines', 'all HSS disciplines']

frequencies = ['annual', 'bimonthly', 'semiweekly', 'daily', 'biweekly', 'semiannual', 'biennial', 'triennial',
               'three times a week', 'three times a month', 'monthly', 'quarterly', 'semimonthly',
               'three times a year', 'weekly', 'continuously updated', 'other']

operations = ['in-house', 'out-sourced', 'both']

column_names_to_fields_mapping = {'ip': {'ISSN': 'A', 'Journal Title': 'B', 'Cluster': 'C', 'Discipline': 'D',
                                         'Owner ROR ID': 'E', 'Publisher ROR ID': 'F',
                                         'APC List Price Range Lower': 'G',
                                         'APC List Price Range Higher': 'H', 'APC List Price Currency': 'I',
                                         'APC Waiver Discount Policy': 'J', 'Subscription List Price Range Lower': 'K',
                                         'Subscription List Price Range Higher': 'L',
                                         'Subscription List Price For Member of The Association of American Universities (in USD)': 'M',
                                         'Subscription List Price Currency': 'N', 'Subscription Discount Policy': 'O',
                                         'Price Transparency Context': 'P', 'Research Articles Published': 'Q',
                                         'Acceptance Rate': 'R', 'Desk Rejection Rate': 'S',
                                         'Issue Publication Frequency': 'T', 'Median Number Reviews': 'U',
                                         'Median Time Submission To First Decision': 'V',
                                         'Median Time Peer Review': 'W',
                                         'Median Time Acceptance To Publication': 'X',
                                         'Counter 5 Unique Item Requests': 'Y',
                                         'Counter 5 Total Item Requests': 'Z',
                                         'Price Breakdown: Journal Community Development': 'AA',
                                         'Price Breakdown: Journal Submission On First Decision': 'AB',
                                         'Price Breakdown: Peer Review': 'AC',
                                         'Price Breakdown: Services Acceptance Publication': 'AD',
                                         'Price Breakdown: Services Post Publication': 'AE',
                                         'Price Breakdown: Platform Development Support': 'AF',
                                         'Price Breakdown: Sales Marketing': 'AG',
                                         'Price Breakdown: Author Customer Support': 'AH', 'Notes': 'AI'},
                                  'foaa': {'ISSN': 'A', 'Journal Title': 'B', 'Cluster': 'C', 'Discipline': 'D',
                                           'Owner ROR ID': 'E', 'Publisher ROR ID': 'F',
                                           'APC List Price Range Lower': 'G',
                                           'APC List Price Range Higher': 'H', 'APC List Price Currency': 'I',
                                           'APC Waiver Discount Policy': 'J',
                                           'Subscription List Price Range Lower': 'K',
                                           'Subscription List Price Range Higher': 'L',
                                           'Subscription List Price For Member of The Association of American Universities (in USD)': 'M',
                                           'Subscription List Price Currency': 'N', 'Subscription Discount Policy': 'O',
                                           'In-house or Outsourced Journal Operations?': 'P', 'Rejection Rate': 'Q',
                                           'Discounts and Waivers Policy': 'R',
                                           'Price Breakdown: Journal Operations': 'S',
                                           'Price Breakdown: Publication': 'T',
                                           'Price Breakdown: Fees': 'U',
                                           'Price Breakdown: Communication': 'V',
                                           'Price Breakdown: General': 'W',
                                           'Price Breakdown: Surplus / Other Revenue': 'X',
                                           'Price Breakdown: Discounts & Waivers': 'Y',
                                           'Notes': 'Z'}}

disciplines = ['1. natural sciences', '1.1. mathematics', '1.2. computer and information sciences',
               '1.3. physical sciences', '1.4. chemical sciences', '1.5. earth and related environmental sciences',
               '1.6. biological sciences', '1.7. other natural sciences', '2. engineering and technology',
               '2.1. civil engineering', '2.2. electrical engineering, electronic engineering, information engineering',
               '2.3. mechanical engineering', '2.4. chemical engineering', '2.5. materials engineering',
               '2.6. medical engineering', '2.7. environmental engineering', '2.8. environmental biotechnology',
               '2.9. industrial biotechnology', '2.10. nano-technology', '2.11. other engineering and technologies',
               '3. medical and health sciences', '3.1. basic medicine', '3.2. clinical medicine',
               '3.3. health sciences', '3.4. medical biotechnology', '3.5. other medical sciences',
               '4. agricultural and veterinary sciences', '4.1. agriculture, forestry, and fisheries',
               '4.2. animal and dairy science', '4.3. veterinary science', '4.4. agricultural biotechnology',
               '4.5. other agricultural sciences', '5. social sciences', '5.1. psychology and cognitive sciences',
               '5.2. economics and business', '5.3. education', '5.4. sociology', '5.5. law',
               '5.6. political science', '5.7. social and economic geography', '5.8. media and communications',
               '5.9. other social sciences', '6. humanities', '6.1. history and archaeology',
               '6.2. languages and literature', '6.3. philosophy, ethics and religion',
               '6.4. arts (arts, history of arts, performing arts, music)', '6.5. other humanities']


# -----------------------------------------------
# Text messages
ISSNS_NOT_FOUND = _("Following ISSN(s) not found in the search.")

# Warnings
NOT_AUTHORIZED_WARNING = _("You are not authorized for the task")
PROCESS_COMPLETED_WARNING = _("The process you are trying has been completed")
DELETED_FILE = _("Deleted {f} framework data for the year {y}")

# Infos
ENTER_TOTP = _("Enter your device generated OTP")
OTP_SENT = _("OTP sent to your email")
OTP_RE_SENT = _("OTP re-sent to your email")
SMS_SENT = _("An SMS with the OTP has been sent to your registered phone number")
SMS_RESENT = _("An SMS with the OTP has been re-sent to your registered phone number")
SUCCESSFUL_UPLOAD = _("Successfully uploaded {f} framework data for the year {y}")
NO_ACCIDENTAL_OVERWRITE = ('A file has already been uploaded with earlier data with the name: "{f}".'
                           ' Please rename the file and try again.')
SMS_BODY = _("{o}\n\n"
             "This is your JCS SMS One Time Passcode which is valid for {m} minutes to login to the JCS dashboard.")
DEACTIVATED = _("Your account has been deactivated by an administrator")

# Emails
OTP_SENT_EMAIL_TITLE = _("JCS OTP")
OTP_SENT_EMAIL_BODY = _("{o}<br/>"
                        "This is your JCS One Time Passcode which is valid for {m} minutes"
                        " to login to the JCS dashboard.")
ACTIVATION_APPROVE_EMAIL_BODY = _("Your account has been activated")
ACTIVATION_REJECT_EMAIL_BODY = _("Your account has been rejected. Contact your admin for any queries")
ACTIVATION_EMAIL_TITLE = _("JCS Account activation")
REJECTION_EMAIL_TITLE = _("JCS Account rejection")
DEACTIVATION_EMAIL_TITLE = _("JCS Account deactivated")
DEACTIVATION_EMAIL_BODY = _("Your cOAlition S Journal Comparison Service account has been deactivated. "
                            "Contact <a href=\"mailto:" + COALITIONS_CONTACT_EMAIL + "\">" + COALITIONS_CONTACT_EMAIL +
                            "</a> for further information.")
DEACTIVATION_EMAIL_BODY_P_USER = _("Your cOAlition S Journal Comparison Service account has been deactivated. "
                                   "Contact your JCS Publisher Administrator \"{admin_email}\" "
                                   "-- for further information.")
DEACTIVATION_EMAIL_BODY_INS_USER = _("Your cOAlition S Journal Comparison Service account has been deactivated. "
                                     "Contact your JCS Administrator \"{admin_email}\" -- for further information.")
PROFILE_SAVED = _("Profile has been saved successfully")
PROFILE_UPDATE_SUBJECT = _("JCS Profile updated")
PROFILE_MOBILE_UPDATE = _("Your mobile number has been successfully updated to {new_mobile}. "
                          "<br/>If you haven't done the update, please inform your JCS Administrator if there is one."
                          "<br/>Otherwise inform <a href=\"mailto:" + COALITIONS_CONTACT_EMAIL + "\">" +
                          COALITIONS_CONTACT_EMAIL + "</a> immediately")
REACTIVATION_EMAIL_TITLE = _("JCS Account reactivated")
NEW_ACCOUNT_EMAIL_TITLE = _("JCS New account request waiting for approval")
NEW_ACCOUNT_EMAIL_BODY = _("New JCS account request has been submitted for approval. Log on to "
                           "<a href=\"" + settings.DOMAIN_NAME + "\">" + settings.DOMAIN_NAME + "</a> to "
                           "approve/reject the request")
NEW_ACCOUNT_BY_UNKNOWN_USER_EMAIL_TITLE = _("JCS New account request by unknown user")
NEW_ACCOUNT_BY_UNKNOWN_USER_EMAIL_BODY = _("New JCS account request has been submitted by unknown user {user} who does "
                                           "not belongs to any group")
SUCCESSFUL_CHANGES = _("Changes saved successfully")
SUCCESSFUL_DEACTIVATION = _("Account deactivated successfully")
SUCCESSFUL_REACTIVATION = _("Reactivation submitted. Review the user to activate")
SUCCESSFUL_PROMOTION = _("User was successfully promoted to administrator level")
PROMOTION_EMAIL_TITLE = _("JCS Account promotion")
PROMOTION_EMAIL_BODY = _("{admin_email} has promoted {new_admin_email}'s cOAlition S Journal Comparison Service account to administrator level.")
SUCCESSFUL_DELETION = _("User deleted successfully")
SUCCESSFUL_PUB_DELETION = _("Publisher and {users} associated user/s deleted successfully")
SUCCESSFUL_ORG_DELETION = _("Organisation and {users} associated user/s deleted successfully")
CONGRATULATE_ACTIVATION = _("Congratulations! Your account on the cOAlition S Journal Comparison Service "
                            "has been activated. Click here <a href=\"" + settings.DOMAIN_NAME + "\">"
                            + settings.DOMAIN_NAME + "</a> to log on. <br/><br/>To log into the system, enter "
                            "your email address on the login page. You will be emailed a pass code. On "
                            "entering this, you will be sent a second one-time code to your registered "
                            "mobile number or access through a third-party authenticator app, which will "
                            "grant you access to the system.")
CONGRATULATE_SPUBLISHER_ACTIVATION = _("Congratulations! Your account on the cOAlition S Journal Comparison Service has"
                                       " been activated. Click here <a href=\"" + settings.DOMAIN_NAME + "\">" +
                                       settings.DOMAIN_NAME + "</a> to log on. <br/><br/>To log into the system, enter "
                                       "your email address on the login page. You will be emailed a pass code. On "
                                       "entering this, you will be sent a second one-time code to your registered "
                                       "mobile number or access through a third-party authenticator app, which will "
                                       "grant you access to the system. Once logged in, you will be able to see your "
                                       "account details, create and approve Publisher User accounts, and upload your "
                                       "price and service data through one of the frameworks. <br/><br/> The Publisher "
                                       "Resources page contains useful information about the process: "
                                       "https://www.coalition-s.org/journal-comparison-service-resources-publishers/.")
MOVE_TO_CONTRACT_SIGN = _("Successfully moved to contract signing")
ACCOUNT_APPROVED = _("Account approved successfully")
ACCOUNT_REJECTED = _("Account rejected successfully")
COMMISERATE_REJECTION = _("Your application to the cOAlition S Journal Comparison Service has been rejected. "
                          "Contact <a href=\"mailto:" + COALITIONS_CONTACT_EMAIL + "\">" + COALITIONS_CONTACT_EMAIL +
                          "</a> for further information.")
COMMISERATE_REJECTION_P_USER = _("Your application to the cOAlition S Journal Comparison Service has been rejected. "
                                 "Contact your JCS Publisher Administrator \"{admin_email}\"- the person who "
                                 "invited you to register to use the service -- for further information.")

ALERT_PUBLISHER_FILE_DELETED_EMAIL_TITLE = _("JCS File deleted")
ALERT_PUBLISHER_FILE_DELETED_EMAIL_BODY = _("A coalition S administrator has deleted the file \"{f}\" which was"
                                            " uploaded by your user {u} on {t}.")
DOWNLOAD_LINK_EMAIL_TITLE = _("JCS download link")
DOWNLOAD_LINK_SUCCESS_MSG = _("JCS data download that you have requested is now available. "
                              "Click <a href=\" {link} \">here</a> or copy the link ( {link} ) to download. <br/>Note that you must login to access"
                              " the link. Login and copy the link in the url to download"
                              "<br/>Download link is valid for " + str(settings.DATA_DUMP_FILES_MAX_AGE) + " days")
DOWNLOAD_LINK_FAILURE_MSG = _("Could not create a download link for your requested download due to some error."
                              "Contact <a href=\"mailto:" + COALITIONS_CONTACT_EMAIL + "\">" + COALITIONS_CONTACT_EMAIL +
                              "</a> for further information with id - ")
NO_DATA_FOR_DOWNLOAD = _("No records found for the data provided")
INVALID_DOWNLOAD_DATA_MSG = _("Error occurred while fetching the records."
                              "Contact <a href=\"mailto:" + COALITIONS_CONTACT_EMAIL + "\">" + COALITIONS_CONTACT_EMAIL +
                              "</a> for further information with id - ")

# Errors
UNKNOWN_ERROR = _("Unknown error occurred. Contact <a href=\"mailto:" + COALITIONS_CONTACT_EMAIL + "\">" +
                  COALITIONS_CONTACT_EMAIL + "</a> for further information with id - ")
INVALID_OTP_ENTERED = _("Invalid OTP entered. Please try again.")
EMAIL_NOT_SENT = _("Server error. Email could not be sent. Contact <a href=\"mailto:" + COALITIONS_CONTACT_EMAIL + "\">"
                   "" + COALITIONS_CONTACT_EMAIL + "</a> for further information. with id - ")
SESSION_EXPIRED = _("Your session expired")
OTP_EXPIRED = _("Your OTP has expired. OTPs are valid for {m} minutes. Please try again."
                .format(m=settings.OTP_VALID_MINUTES))
USER_DOES_NOT_EXIST = _("Could not retrieve user details")
PUBLISHER_NOT_VERIFIED = _("Publisher account not verified. "
                           "Contact " + COALITIONS_CONTACT_EMAIL + " for further information.")
ACCOUNT_NOT_ACTIVE = _("Your account is not active. You cannot login until your account is active.")
INVALID_FORM = _("Invalid details entered. Enter valid details.")
SMS_ERROR = _("Unable to deliver SMS. Reason: ")
ONE_GROUP = _("This user either belongs to more than one group or"
              " has not yet been assigned to a group and cannot log in.")
PUBLISHER_EMAIL_REQUIRED = _("Enter the publisher user email to whom you are generating the link")
INS_USER_EMAIL_REQUIRED = _("Enter the institutional user email to whom you are generating the link")
PUBLISHER_EMAIL_DOEST_NOT_MATCH = _("Email id does not match to the email id specified for the "
                                    "link to create the publisher user")
ALREADY_MEMBER_OF_JCS = _("You are already member of cOAlition S Journal Comparison Service. "
                          "Contact " + COALITIONS_CONTACT_EMAIL + " for further information.")
DOES_NOT_HAVE_ORGANISATION = _("The user does not belong to any organisation")
INASP_FORM_ERROR = _("You must indicate which INASP platform your journal is indexed by.")
ISSN_FORM_ERROR = _("You must supply a valid ISSN.")
SPREADSHEET_CORRECT = _("Please correct and resubmit.")
P_USER_LINK_EXPIRED = _("The link to create new Publisher User has expired. "
                        "The link is valid for {no_of_days} days only. "
                        "Contact your JCS Publisher Administrator for further information.").\
                        format(no_of_days=settings.P_USER_LINK_VALID_IN_DAYS)
INVALID_LINK = _("This link is no longer valid.")
INVALID_DOWNLOAD_DATA = _("Invalid data. Cannot process with download of records")
RATE_LIMIT_EXCEEDED = _("You have made too many requests to submit data during the login process. "
                        "You will next be able to submit data in half an hour.")

# Spreadsheet messages
SPREADSHEET_TITLE_MSG = (_('does not have a title'), _('do not have titles'))
SPREADSHEET_ISSN_MSG = (_('does not contain a valid ISSN'), _('do not contain valid ISSNs'))
SPREADSHEET_INT_MSG = (_('does not contain an integer'), _('do not contain integers'))
SPREADSHEET_CURRENCY_MSG = (_('does not contain a valid ISO-4217 currency code'),
                            _('do not contain valid ISO-4127 currency codes'))
SPREADSHEET_DISCIPLINE_MSG = (_('does not contain a valid discipline'),
                              _('do not contain a valid discipline'))
SPREADSHEET_PERCENTAGE_MSG = (_('does not contain a percentage between 0 and 100%'),
                              _('do not contain a percentage between 0 and 100%'))
SPREADSHEET_FREQUENCY_MSG = (_('does not contain a valid issue publication frequency'),
                             _('do not contain valid issue publication frequencies'))
SPREADSHEET_DECIMAL_MSG = (_('does not contain a valid decimal'), _('do not contain valid decimals'))
SPREADSHEET_OPERATIONS_MSG = (_('does not contain a valid operation'), _('do not contain valid operations'))
SPREADSHEET_URL_MSG = (_('does not contain a valid URL'), _('do not contain valid URLS'))

# these require an extra space in front for padding reasons.
SPREADSHEET_DISCIPLINE_EXTRA = _(" You must enter a valid discipline as listed "
                                 "<a href=\"https://read.oecd-ilibrary.org/science-and-technology/frascati-manual-2015_9789264239012-en#page61\">here</a> "
                                 "or \'{}\'.".format('\', \''.join(all_disciplines)))
SPREADSHEET_DECIMAL_EXTRA = _(" A period (dot) should be used as the decimal separator."
                              " No thousand separator should be used.")
SPREADSHEET_FREQUENCY_EXTRA = _(" Please choose one of: <i>'{}'</i>.".format('\', \''.join(frequencies)))
SPREADSHEET_OPERATIONS_EXTRA = _(" Please choose one of: <i>'{}'</i>.".format('\', \''.join(operations)))
SPREADSHEET_URL_EXTRA = _(' A valid URL is defined as including a scheme, either "http" or "https", followed by '
                          '"://" and to be in total 500 characters or less.')
SPREADSHEET_ISSN_DUPLICATES = 'User: {user}, {publisher} just uploaded {issn} ISSN\\s that already exist/s, ' \
                  'having been uploaded by {other_publisher} for the year {other_issn_year}.\n' \
                  'List of duplicate ISSN/s:\n{issn_list}' \

# Registration errors
NO_OTHER_SERVICE = _("You must submit a name for the other service that indexes this journal.")
NO_TRADE_BODIES = _("You must indicate which Publisher Trade body you are a member of.")
NO_OTHER_TRADE_BODY = _("You must submit a name for the other Publisher trade body you are a member of.")

# DB errors
EMAIL_CONSTRAINT = _("Email already exists")
PUBLISHER_CONSTRAINT = _("The email address you entered is already associated with a publisher. "
                         "Contact <a href=\"mailto:" + COALITIONS_CONTACT_EMAIL + "\">" + COALITIONS_CONTACT_EMAIL +
                         "</a> for further information.")
ORGANISATION_CONSTRAINT = _("The email address you entered is already associated with an organisation. "
                            "Contact <a href=\"mailto:" + COALITIONS_CONTACT_EMAIL + "\">" + COALITIONS_CONTACT_EMAIL +
                            "</a> for further information.")

# User login Errors
PUBLISHER_USERS_ONLY = _("You must login as Publisher to access the page")
INSTITUTIONAL_USERS_ONLY = _("You must login as Institutional User to access the page")

# Constant Names
USER_TYPE_INSTITUTIONAL = _("Institutional")
USER_TYPE_INSTITUTION = _("Institution")
USER_TYPE_PUBLISHER = _("Publisher")

# Frameworks
FRAMEWORK_IP = "ip"
FRAMEWORK_FOAA = "foaa"
INFORMATION_POWER = "Information Power"
FAIR_OPEN_ACCESS_ALLIANCE = "Fair Open Access Alliance"

# Audit Trail logs messages
VISIT_ACTION = 'Visit'
DOWNLOAD_ACTION = 'Download'
QUERY_DOWNLOAD_ACTION = 'QueryDownload'
COMPARE_ACTION = 'Compare'
DOWNLOAD_BY_QUERY = 'Download request by query {query}'
DOWNLOAD_FROM_COMPARE = 'Download request from compare'
DOWNLOAD_FROM_JOURNAL = 'Download request from journal page'
DOWNLOAD_BY_ISSN = 'Download request from the issn list'
DOWNLOAD_ALL_JOURNALS = "Download all journals"

# session objects
PREVIOUS_URL = "previous_url"

# Registration constants
TOTAL_STEPS_ADMIN_REGISTRATION = '8'
TOTAL_STEPS_USER_REGISTRATION = '6'
