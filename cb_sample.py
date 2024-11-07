import sqlite3
from datetime import datetime
from email_sender import send_email
from enum import Enum
from PyRTF.document.section import *
from PyRTF.Elements import *
from PyRTF.document.paragraph import *
from PyRTF.PropertySets import *
from PyRTF.Styles import *
import logging

# Constants
class DaysRange(Enum):
    NONE = -1
    DAILY = 1
    WEEKLY = 7
    MONTHLY = 30

# Configuration
DATABASE_FILE = "cbdb.db"
REPORT_PREFIX = "ClientBoxx"

# Logging
logging.basicConfig(filename="report.log", level=logging.INFO)

# Function to execute a query and return results with date range
def execute_query_with_date_range(cur, query, headers, date_range):
    try:
        if date_range > 0:
            query = query.replace("date_range", str(date_range))
        
        cur.execute(query)
        
        row_data = cur.fetchall()
        if row_data:
            return row_data
        else:
            return "** NO DATA **"
    except sqlite3.Error as e:
            logging.error(f"Error executing query: {str(e)}")
            raise

def execute_query_total_storage(cur):
    try:
        query = 'select round(sum(file_size)/1000000000,2) as "storage in GB" from attachment'
        cur.execute(query)
        row_data = cur.fetchone()
        
        if row_data is not None:
            sumStorage = str(row_data[0])
            return sumStorage
        else:
            return "** NO DATA **"
    except sqlite3.Error as e:
        logging.error(f"Error executing query: {str(e)}")
        raise

# Create RTF document and sections
def create_rtf_document():
    doc = Document()
    section = Section()
    doc.Sections.append(section)
    return doc, section

# Add header to the document
def add_document_header(section, report_date):
    section.append("==========================================")
    section.append(f"ClientBoxx Usage Report: {report_date}")
    section.append("==========================================")
    section.append('')
    section.append('')

# Add section title to the document
def add_section_title(section, section_name):
    section.append(f"{REPORT_PREFIX} {section_name}:")

# Create and add table to the section
def add_table_to_section(section, headers, data_rows):
    table = Table()
    table.ColumnCount = len(headers)
    header_cells = [Cell(Paragraph(str(value))) for value in headers]
    table.AddRow(*header_cells)
    
    for data_row in data_rows:
        data_cells = [Cell(Paragraph(str(value))) for value in data_row]
        table.AddRow(*data_cells)
    
    section.append(table)
    section.append('')

# Define reporting sections and their properties with configurable date ranges
report_sections = [
    {
        "name": "New Users in past date_range days",
        "query": 'select distinct u.id, u.name, u.email, u.phone, u.created_at, count(cu.client_id) as "client count", julianday(\'now\') - julianday(u.created_at) as "account age" from "user" as u, client_user as cu where u.id = cu.user_id and julianday(\'now\') - julianday(u.created_at) < date_range group by u.id order by u.name',
        "headers": [
            "ID",
            "Name",
            "Email",
            "Phone",
            "Created On",
            "Client Count",
            "Account Age",
        ],
        "date_range": DaysRange.MONTHLY.value,  # Configurable date range in days
    },
    {
        "name": "User Listing",
        "query": 'select distinct u.id, u.name, u.email, u.phone, u.created_at, count(cu.client_id) as "client count" from "user" as u, client_user as cu where u.id = cu.user_id group by u.id order by u.name',
        "headers": ["ID", "Name", "Email", "Phone", "Created On", "Client Count"],
        "date_range": DaysRange.NONE.value,  # No date range required
    },
    {
        "name": "Storage Details",
        "query": 'select distinct u.id, u.name, u.email, u.phone, u.created_at, count(at.id), round(sum(at.file_size)/1000000000,2) from "user" as u, attachment as at where u.id = at.user_id group by u.id order by u.name',
        "headers": [
            "ID",
            "Name",
            "Email",
            "Phone",
            "Created On",
            "Attachment Count",
            "Storage GB",
        ],
        "date_range": DaysRange.NONE.value,  # No date range required
    },
    {
        "name": "Attachment Details",
        "query": "select distinct u.id, u.name, u.email, u.phone, u.created_at, count(at.id) as \"attachment count\", case when cast(at.type as char) like '%1%' then 'doc' when cast(at.type as char) like '%2%' then 'img' when cast(at.type as char) like '%3%' then 'vid' when cast(at.type as char) like '%4%' then 'note' else cast(at.type as char) end as \"type\", round(sum(at.file_size)/1000000000,2) as \"storage in GB\" from \"user\" as u, attachment as at where u.id = at.user_id group by u.id, at.type order by u.name,\"attachment count\" desc, \"storage in GB\" desc",
        "headers": [
            "ID",
            "Name",
            "Email",
            "Phone",
            "Created On",
            "Attachment Count",
            "Type",
            "Storage GB",
        ],
        "date_range": DaysRange.NONE.value,  # No date range required
    },
]

# Main function
def main():
    try:
        # Connect to the ClientBoxx database (local test instance)
        conn = sqlite3.connect(DATABASE_FILE)
        logging.info("Connected to database")
        
        now = datetime.now()
        report_date = now.strftime("%d/%m/%Y %H:%M")
        report_file_name = f"cb_user_report_{now.strftime('%d%m%Y%H%M%S')}.rtf"
        
        doc, section = create_rtf_document()
        
        # Add document header
        add_document_header(section, report_date)
        
        try:
            cur = conn.cursor()
            
            for section_data in report_sections:
                section_name = section_data["name"].replace("date_range", str(section_data["date_range"]))
                add_section_title(section, section_name)
                query_result = execute_query_with_date_range(cur, section_data["query"], section_data["headers"], section_data["date_range"])
                add_table_to_section(section, section_data["headers"], query_result)
            
            # Add total storage section
            section.append('')
            total_storage_result = execute_query_total_storage(cur)
            section.append(f"{REPORT_PREFIX} Total Storage: {total_storage_result}")
            section.append('')
            
            # Save the RTF document
            doc.write(report_file_name)
            
            # Email the report
            send_email(
                       report_file_name,
                       "CB Report",
                       "muhammad.zaman.engg@gmail.com",
                       "muhammad.zaman.engg@gmail.com",
                       "muhammad.zaman.engg@gmail.com",
                       "",  # Required App Specific Password
                       report_file_name
                       )
        
        finally:
            cur.close()

    except (Exception, sqlite3.DatabaseError) as error:
      logging.error(error)

    finally:
        if conn is not None:
          conn.close()

if __name__ == "__main__":
    main()
