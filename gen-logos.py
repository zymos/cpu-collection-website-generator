#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
CHIPS - CPUU Graveyard: upload script

This script will take a CSV spreadsheet with details on files to upload


input is CSV spreadsheetfile and image dir

USAGE: python chips-pages.py [CSV_FILE] [IMAGES_DIR]

run this script in the photos dir?


'''

from pprint import pprint
from collections import defaultdict
from requests.utils import quote
import stat
import re
import urllib
import csv
import sys
import os
import time


############################################################################
# Config
#



#  OVERWRITE = True


userpass_location = '/home/zymos/.config/'
domain = 'happytrees.org'
urlpath = '/sites/chips-mw-1.39.0/'




# Testinge
#  E_CHIPS = False
#  E_MANUF = False
#  E_MANUF_FAM = False
#  E_CATS = True
#  E_UPLOAD_IC = False
#  E_REDIRECTS = False
#  E_FAMILY = False
#  E_STATS = False
#  E_TRADE = True

TEST = False
TEST_100 = False
NO_OVERWRITE_PAGE = False
NO_OVERWRITE_UPLOAD = True

E_LOGO = False
E_UPLOAD = False
#

E_LOGO = True
#  E_UPLOAD = True
#  skip_lines=1


############################################################################
# Code
#

if TEST:
    E_CHIPS = False
    E_MANUF = False
    E_MANUF_FAM = False
    E_CATS = False
    E_UPLOAD = False
    E_REDIRECTS = False
    E_FAMILY = False
    E_STATS = False
    E_TRADE = False
    E_LOGO = False




def writefile(filename, contents):

    #  filename = 'scripts/' + re.sub(r'/', '_', filename)
    fo = open(filename, "w")
    fo.write(contents)
    fo.close()





def login():

    # mediawiki bot module
    from mwclient import Site

    # import external user/pass file in 'userpass_location'
    # chips.py file contains userpass() function returning (username, password)
    sys.path.insert(0, userpass_location)
    import chips

    # get user/pass from external file
    (username, password) = chips.userpass()

    # set site
    ua = 'MyCoolTool/0.2 (xyz@example.org)'
    site = Site(domain, path=urlpath,  clients_useragent=ua)

    # login
    print("Logging in: " + username)
    try:
        site.login(username, password)
    except Exception as e:
        print("Login failed" + str(e))
        sys.exit(1)

    return site
# end: login()





def editpage(site, pagename, text):

    import time
    # set pagename

    #  pagename = "[asdasdasd]"
    if re.search(r'[\[\]\#\}\{\|]', pagename):
        print("Error: pagename contains invalid char: \"" + pagename + "\", skipping")
    else:
        
        # remove all extra white space
        pagename = re.sub(r'\s+', ' ', pagename).strip()

        # generate page
        if not TEST:
            page = site.pages[pagename]

        if page.exists and NO_OVERWRITE_PAGE:
            return

        # write page
        print('  > Writing page: ' + pagename)
        if not TEST:
            try:
                page.edit(text, 'Bot upload page')
            except Exception as e:
                print("Edit failed" + str(e))
                sys.exit(1)



    # dont hammer server
    if not TEST:
        time.sleep(1)

# end: editpage()






def upload_file(site, filename, filename_out, description):
    '''Upload file to MediaWiki'''

    import time

    pagename = "File:" + filename_out

    if os.path.exists(filename):
        page = site.pages[pagename]
        if not page.text() == '' and NO_OVERWRITE_UPLOAD:
            return # exit if no overwrite upload
        site.upload(open(filename, 'rb'), filename_out, description)
    else:
        print("Error: file DNE, " + filename)

    # dont hammer, not hammer time
    time.sleep(1)

# end: upload_file()



def upload_logo(site, logo_dir, details):
    '''Uploading logos'''

    (manuf, fam, fam2, fam3, filename) = details
    
    filename_loc =  os.path.join(logo_dir, filename)
   
    print(filename)

    #  file_out = os.path.basename(file)
    text = "{{logo-file-page\n"
    text += "|manufacturer=" + manuf + "\n"
    text += "|fam=" + fam + "\n"
    text += "|fam2=" + fam2 + "\n"
    text += "|fam3=" + fam3 + "\n"
    text += "}}\n"

    upload_file(site, filename_loc, filename, text)

    time.sleep(0.5)

# end: upload_logo()



def upload_chip(site, image_dir, details):
    '''Upload chips'''

    (manuf, family, part, filename) = details

    filename_loc =  os.path.join(image_dir, filename)

    pprint(details)
    print(filename_loc)
    text = "{{chip-image-page"
    text += "\n|manufacturer=" + manuf
    text += "\n|family=" + family
    text += "\n|part=" + part
    text += "\n}}"

    upload_file(site, filename_loc, filename, text)

# end: upload_chip()




def sort_family_list():
    '''sort family list in logical order'''

    #  {|class="wikitable sortable"
    #  !Name and surname!!Rank
    #  |-
    #  |data-sort-value="Smith, John"|John Smith||data-sort-value="16"|[[Corporal|Cpl]]
    #  |-
    #  |data-sort-value="Ray, Ian"|Ian Ray||data-sort-value="8"|[[Captain (OF-2)|Capt]]
    #  |-
    #  |data-sort-value="Bianchi, Zachary"|Zachary Bianchi||data-sort-value="10"|[[2nd Lieutenant|2 Lt]]
    #  |}






# End: sort_family_list()

def generate_comma_seperated_page_txt(input_text, output_page_text):
    #  page_txt=''
    page = {}
    #  print("in: " + input_text)
    input_str_list = input_text.split(',')
    #  print(input_str_list)
    for page_name in input_str_list:
        #  print(" >" + page_name)
        page_name_fixed = re.sub('^ ', '', page_name)
        text = output_page_text
        #  writefile(filename, text)
        title = 'Category:' + page_name_fixed

        #  print("page title " + page_name_fixed)
        #  print("title " + title)
        #  page_txt += "{{-start-}}\n'''" + title + "'''\n"
        #  page_txt += text
        #  page_txt += "{{-stop-}}\n"
        page.update({title: text})
    return page


def chip_csv_file(filename):
    # open CSV file
    with open(filename, "r") as f:

        chip_data = []

        data = csv.reader(f, delimiter=",")
        #  for row in data:
        #     print(row[0])
        #  exit

        # initalize

        # In script: Changed to script dir
        #  script_text += 'cd scripts/\n\n'
        #  page_txt = ''

        line = 0
        # read each line of CSV
        for row in data:
            # filename_out = row[0] + '_-_' + row[4] + '.txt'

            #  print("row" + str(line) + str(row))

            # skips the lables
            # line += 1
            # if(line <= skip_lines):
            #    continue

            #
            #  photo_type=row[0]
            #  manufacturer=row[1]
            #  family=row[2]
            #  sub_family=row[3]
            #  chip_type=row[4]
            #  name = row[5]
            #  part_number=row[6]
            #  core_id=row[7]
            #  number_of_cores=row[8]
            #  die_size = row[9]
            #  trans=row[10]
            #  tech=row[11]
            #  image_file=row[12]
            #  license=row[13]
            #  image_creator=row[14]
            #  photo_source=row[15]
            #  #  blank [16]
            #  high_res_link=row[17]
            #  notes=row[18]
            #  tags=row[19]
            #  my_notes=row[20]

            # find the col for each var in dict
            if line == 0:
                col = 0
                for entry in row:
                    #  print(str(col) + "(" + entry + ")")
                    if (entry == "Manuf"):
                        Manuf_line = col
                    elif (entry == "Fam"):
                        Fam_line = col
                    elif (entry == "Fam2"):
                        Fam2_line = col
                    elif (entry == "Fam3"):
                        Fam3_line = col
                    elif (entry == "Logo"):
                        Logo_line = col
                    elif (entry == "Logo2"):
                        Logo2_line = col
                    elif (entry == "Logo3"):
                        Logo3_line = col
                    elif (entry == "Logo4"):
                        Logo4_line = col
                    elif (entry == "Logo5"):
                        Logo5_line = col
                    elif (entry == "Logo6"):
                        Logo6_line = col
                    elif (entry == "Logo7"):
                        Logo7_line = col
                    elif (entry == "Logo8"):
                        Logo8_line = col
                    col += 1
            # end detect the column

            # add new chip to array
            else:
                chip_data.append({
                    "Manuf": row[Manuf_line],
                    "Fam": row[Fam_line],
                    "Fam2": row[Fam2_line],
                    "Fam3": row[Fam3_line],
                    "Logo": row[Logo_line],
                    "Logo2": row[Logo2_line],
                    "Logo3": row[Logo3_line],
                    "Logo4": row[Logo4_line],
                    "Logo5": row[Logo5_line],
                    "Logo6": row[Logo6_line],
                    "Logo7": row[Logo7_line],
                    "Logo8": row[Logo8_line]})
                # end append
            # end if/else
            # increment line number for CSV file
            #  print(line)
            line += 1

    #  print(chip_data)
    return chip_data
# end csv


##########################################################
# chip page
#
def chip_page(chip):

    #  text = "{{-start-}}\n"
    #  text += "'''" + chip_single["Manufacturer"] + "'''\n"


    # remove extra white spaces
    chip_single = {}
    for param in chip.keys():
        chip_single[param] = re.sub(r'\s+', ' ', chip[param]).strip()



    # generate title
    if not chip_single["title"] == '':
        title = chip_single["title"]
    elif not chip_single["Manufacturer"] == '' and not chip_single["Part"] == '':
        title = chip_single["Manufacturer"] + " - " + chip_single["Part"]
    else:
        # title blank, will skip
        title = ''


    text = ''
    text += "{{chip-box\n"
    text += "|New = " + chip_single["New"] + "\n"
    text += "|title = " + chip_single["title"] + "\n"
    text += "|owned = " + chip_single["owned"] + "\n"
    text += "|Trade = " + chip_single["Trade"] + "\n"
    text += "|Manufacturer = " + chip_single["Manufacturer"] + "\n"
    text += "|Part = " + chip_single["Part"] + "\n"
    text += "|Label_ID = " + chip_single["Label_ID"] + "\n"
    text += "|Alt_ID_1 = " + chip_single["Alt_ID_1"] + "\n"
    text += "|Alt_ID_2 = " + chip_single["Alt_ID_2"] + "\n"
    text += "|Alt_ID_3 = " + chip_single["Alt_ID_3"] + "\n"
    text += "|Type = " + chip_single["Type"] + "\n"
    text += "|Family = " + chip_single["Family"] + "\n"
    text += "|Sub_Family = " + chip_single["Sub_Family"] + "\n"
    text += "|sub_family2 = " + chip_single["sub_family2"] + "\n"
    text += "|sub_family3 = " + chip_single["sub_family3"] + "\n"
    text += "|Core = " + chip_single["Core"] + "\n"
    text += "|CPUID = " + chip_single["CPUID"] + "\n"
    text += "|Instruction_set = " + chip_single["Instruction_set"] + "\n"
    text += "|IS_Ext = " + chip_single["IS_Ext"] + "\n"
    text += "|Instruction_link = " + chip_single["Instruction_link"] + "\n"
    text += "|Computer_architecture = " + \
        chip_single["Computer_architecture"] + "\n"
    text += "|ISA = " + chip_single["ISA"] + "\n"
    text += "|Microarchitecture = " + chip_single["Microarchitecture"] + "\n"
    text += "|Designer_of_Core = " + chip_single["Designer_of_Core"] + "\n"
    text += "|Clone = " + chip_single["Clone"] + "\n"
    text += "|Cores = " + chip_single["Cores"] + "\n"
    text += "|Pipeline = " + chip_single["Pipeline"] + "\n"
    text += "|Multiprocessing = " + chip_single["Multiprocessing"] + "\n"
    text += "|Architecture = " + chip_single["Architecture"] + "\n"
    text += "|Bus_Width = " + chip_single["Bus_Width"] + "\n"
    text += "|Address_Width = " + chip_single["Address_Width"] + "\n"
    text += "|Speed = " + chip_single["Speed"] + "\n"
    text += "|Bus_speed = " + chip_single["Bus_speed"] + "\n"
    text += "|Bus_type = " + chip_single["Bus_type"] + "\n"
    text += "|Clock_multiplier = " + chip_single["Clock_multiplier"] + "\n"
    if re.search('external', chip_single["FPU"]):
        fpu =   chip_single["FPU"] 
    elif re.search('ext', chip_single["FPU"]):
        fpu =  re.sub('ext', 'external', chip_single["FPU"] )
    else:
        fpu =   chip_single["FPU"] 
    text += "|FPU = " + fpu + "\n"
    text += "|GPU = " + chip_single["GPU"] + "\n"
    text += "|DSP = " + chip_single["DSP"] + "\n"
    text += "|L1_cache = " + chip_single["L1_cache"] + "\n"
    text += "|L1_shared = " + chip_single["L1_shared"] + "\n"
    text += "|L1_data = " + chip_single["L1_data"] + "\n"
    text += "|L1_instruction = " + chip_single["L1_instruction"] + "\n"
    text += "|L2_cache = " + chip_single["L2_cache"] + "\n"
    text += "|L3_cache = " + chip_single["L3_cache"] + "\n"
    text += "|ROM_Int = " + chip_single["ROM_Int"] + "\n"
    text += "|ROM_type = " + chip_single["ROM_type"] + "\n"
    text += "|RAM_Int = " + chip_single["RAM_Int"] + "\n"
    text += "|RAM_Max = " + chip_single["RAM_Max"] + "\n"
    text += "|RAM_type = " + chip_single["RAM_type"] + "\n"
    text += "|Package = " + chip_single["Package"] + "\n"
    text += "|Package_Size = " + chip_single["Package_Size"] + "\n"
    text += "|Socket = " + chip_single["Socket"] + "\n"
    text += "|Transistors = " + chip_single["Transistors"] + "\n"
    text += "|Process_Size = " + chip_single["Process_Size"] + "\n"
    text += "|Technology = " + chip_single["Technology"] + "\n"
    text += "|Die_Size = " + chip_single["Die_Size"] + "\n"
    text += "|Vcc = " + chip_single["Vcc"] + "\n"
    text += "|Vcc_range = " + chip_single["Vcc_range"] + "\n"
    text += "|Vcore = " + chip_single["Vcore"] + "\n"
    text += "|Vcc__I_O_ = " + chip_single["Vcc__I_O_"] + "\n"
    text += "|V_I_O__secondary = " + chip_single["V_I_O__secondary"] + "\n"
    text += "|V_I_O__tertiary = " + chip_single["V_I_O__tertiary"] + "\n"
    text += "|Power_min = " + chip_single["Power_min"] + "\n"
    text += "|Power_typ = " + chip_single["Power_typ"] + "\n"
    text += "|Power_max = " + chip_single["Power_max"] + "\n"
    text += "|TDP = " + chip_single["TDP"] + "\n"
    text += "|Low_power_modes = " + chip_single["Low_power_modes"] + "\n"
    text += "|Grade = " + chip_single["Grade"] + "\n"
    text += "|Date_Introduced = " + chip_single["Date_Introduced"] + "\n"
    text += "|Year = " + chip_single["Year"] + "\n"
    text += "|Initial_price = " + chip_single["Initial_price"] + "\n"
    text += "|Applications = " + chip_single["Applications"] + "\n"
    text += "|Features = " + chip_single["Features"] + "\n"
    text += "|Rarity = " + chip_single["Rarity"] + "\n"
    text += "|Description = " + chip_single["Description"] + "\n"
    text += "|Photo_1 = " + chip_single["Photo_1"] + "\n"
    text += "|Photo_2 = " + chip_single["Photo_2"] + "\n"
    text += "|Photo_3 = " + chip_single["Photo_3"] + "\n"
    text += "|Photo_4 = " + chip_single["Photo_4"] + "\n"
    text += "|Photo_5 = " + chip_single["Photo_5"] + "\n"
    text += "|Photo_die = " + chip_single["Photo_die"] + "\n"
    text += "|Photo_die_license = " + chip_single["Photo_die_license"] + "\n"
    text += "|Datasheet = " + chip_single["Datasheet"] + "\n"
    text += "|Reference_1 = " + chip_single["Reference_1"] + "\n"
    text += "|Reference_2 = " + chip_single["Reference_2"] + "\n"
    text += "|Reference_3 = " + chip_single["Reference_3"] + "\n"
    text += "|Reference_4 = " + chip_single["Reference_4"] + "\n"
    text += "}}\n"

    #  text += "{{-stop-}}\n"

    return (title, text)
# end chip_page


def manufacturer_page(manufacturers):

    text = ''

    title = 'Manufacturers'

    #  text += "{{manuf-box\n"
    #  text += "|manuf" + manuf + "\n"
    #  text += "}}\n\n"
    #  text += "\n"
    text += "{{manuf-list\n"

    # create list
    x = 0
    for manuf, count in manufacturers.items():
        text += "|manuf-" + str(x) + " = " + manuf + "\n"
        text += "|manuf-" + str(x) + "-count = " + str(count) + "\n"
        x += 1

    text += "}}\n"
    text += "[[category:main]]\n"
    #  text += "{{-stop-}}\n"

    return (title, text)

# end manufacturer_page


# Create indiviual manufacturer page with list of families
def all_manufacturer_pages(manuf, manufacturer_family):

    title = manuf

    text = ''

    # summary box
    text += "{{manuf-page\n"
    text += "|manufacturer = " + manuf + "\n"
    text += "}}\n\n"
    text += "\n"

    # list
    text += "{{manuf-family-list\n"
    text += "|manuf = " + manuf + "\n"

    # create list
    x = 0
    for family, count in manufacturer_family[manuf].items():
        text += "|family-" + str(x) + " = " + family + "\n"
        text += "|family-" + str(x) + "-count = " + str(count) + "\n"
        x += 1

    text += "}}\n"
    text += "[[category:manufacturers]]\n"

    return (title, text)

# end manufacturer_page()






def family_pages(family_name, count, chips):
    '''Individual family pages'''

    text = ''

    title = family_name + ' family'

    text += '{{Family-page\n'

    text += '|family = ' + family_name + '\n'
    text += '|count = ' + str(count) + '\n'
    text += '}}'

    text += '{{Family-chips-list'
    x = 0
    for chip in  chips:
        text += '|chip-' + str(x) + ' = ' + chip + '\n'
        #  text += '|manuf-fam-count-' + str(x) + ' = ' + chip + '\n'
        x += 1
    #  text += "}}\n"


    x = 0
    #  for chip in  family:
        #  text += '|manuf-' + str(x) + ' = ' + manuf[x] + '\n'
        #  text += '|chip-' + str(x) + ' = ' + chips[x] + '\n'
        #  x += 1
    text += "}}\n"

    return (title, text)
# end: family_page()






def manufacturer_family_pages(title, chips):

    #  title = manuf + " - " + family + ' family'

    manuf = chips[0][0]
    family = chips[0][1]

    # manuf and family should be same for all chips in list
    # summary
    text = '{{manuf-family-page\n'
    text += "|manufacturer = " + manuf + "\n"
    text += "|family = " + family + "\n"
    text += "}}\n\n"

    #  list
    text += "{{chip-list\n"
    x = 0
    #  print(manuf + family)
    for chip in chips:
        #  pprint(chip)
        text += "|chip-" + str(x) + " = " + chip[2] + "\n"
        x += 1

    text += "}}\n"

    #  print(text)
    return (title, text)
# end: manuf_family_pages()


# Utility function to create multi-dimentionsion dictionary
def multi_dict(K, type):
    if K == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: multi_dict(K-1, type))
# end: multi_dict




# Create pleasing looking units
def unit_fix(value, unit):

    units = {}
    
    # force string
    value = str(value)

    # units and regex replacements
    units['frequency'] = [
        [r"[Kk]$", " kHz", re.IGNORECASE],
        [r"[gG]$", " GHz", re.IGNORECASE],
        [r"[mM]$", " MHz", re.IGNORECASE],
        [r"[kK][hH][zZ]$", " kHz", re.IGNORECASE],
        [r"[mM][hH][zZ]$", " MHz", re.IGNORECASE],
        [r"[gG][hH][zZ]$", " GHz", re.IGNORECASE],
        [r"[hH][zZ]$", " Hz", re.IGNORECASE]
        ]

    units['length'] = [
        ["[Cc][Uu]$", "Cu", re.IGNORECASE],
        ["[uU][mM]$", " µm", re.IGNORECASE],
        ["[uU]$", " µm", re.IGNORECASE],
        #  ["U$", " µm", re.IGNORECASE],
        ["µ[mM]$", " µm", re.IGNORECASE],
        ["[mM][mM]$", " mm", re.IGNORECASE],
        ["[nN][mM]$", " nm", re.IGNORECASE],
        ["[nN]$", " nm", re.IGNORECASE],
        ["[iI][nN]$", " in", re.IGNORECASE],
        ["[cC][mM]$", " cm", re.IGNORECASE]
        ]

    units['area'] = [
        ["mm2$", " mm<sup>2</sup>", re.IGNORECASE],
        ["mm^2$", " mm<sup>2</sup>", re.IGNORECASE],
        ["um2$", " µm<sup>2</sup>", re.IGNORECASE],
        ["um^2$", " µm<sup>2</sup>", re.IGNORECASE],
        ["µm2$", " µm<sup>2</sup>", re.IGNORECASE],
        ["µm^2$", " µm<sup>2</sup>", re.IGNORECASE],
        ["cm2$", " cm<sup>2</sup>", re.IGNORECASE],
        ["cm^2$", " cm<sup>2</sup>", re.IGNORECASE],
        ["in2$", " in<sup>2</sup>", re.IGNORECASE],
        ["in^2$", " in<sup>2</sup>", re.IGNORECASE]
        ]

    units['bit'] = [
        [r'([0-9])$', r"\1-bit", re.IGNORECASE],
        ["[bB]$", "-bit", re.IGNORECASE]
        ]

    units['bit_byte'] = [
        ["external", "external", re.IGNORECASE],
        ["ext", "external", re.IGNORECASE],
        ["b$", " bits", 0],
        ["B$", " bytes", 0],
        ["[kK][bB]$", " KiB", re.IGNORECASE],
        ["[kK]$", " KiB", re.IGNORECASE],
        ["[mM]$", " MiB", re.IGNORECASE],
        ["[mM][bB]$", " MiB", re.IGNORECASE],
        ["[gG]$", " GiB", re.IGNORECASE],
        ["[gG][bB]$", " GiB", re.IGNORECASE],
        ["[tT]$", " TiB", re.IGNORECASE],
        ["[tT][bB]$", " TiB", re.IGNORECASE]
        ]

    #  correct prefered syntax
    if unit in units.keys():
        for inst in units[unit]:
            #  print(value + inst[0] + inst[1])
            if re.search(inst[0], value, inst[2]):
                #  print("ping"+value + inst[0] + inst[1])
                if inst[2] == 0: # case sensitive
                    value = re.sub(inst[0], inst[1], value)
                else:
                    #  print("z")                                                  
                    value = re.sub(inst[0], inst[1], value, re.IGNORECASE)
                break # escapes loop if match is found first, so list is prioitize

    # remove multispaces
    value = re.sub(' +', ' ', value)

    return value
# end: unit_fix()







def is_na(param):
    ''' this detect a entry of NA in its vary forms'''
    for p in ['', 'NA', 'na', 'Na', 'nA', 'x', 'X', 0, '0', 'none', 'None', 'NONE', 'no', 'NO', 'No']:
        #  print("arg")
        if param == p:
            return True
    return False
# end: is_na()



def create_fam_logo_page(upload_ic):
    '''Creates the family logo page'''

    text = '<gallery widths=80px heights=80px caption="family logos">\n'

    for chip_dets in upload_ic:
        text += 'File:' + chip_dets[4] + "| [[" + chip_dets[0] + "]] - [[" + chip_dets[1] + " family|" + chip_dets[1] + "]] "
        text += chip_dets[2] + " " + chip_dets[3] + "\n"
        # chip dets => (manuf, family, part, filename)
        #  if not chip_dets[4] == "": #file is listed
            #  upload_chip(site, image_dir, chip_dets)

    text += "</gallery>\n"

    return text
# end: create_fam_logo_page()




##########################################################
# Main function
def main():

    # first line
    line = 0
    text = ''
    pages_text = ''

    print("")

    #####################
    # inputs

    try:
        filename = sys.argv[1]
    except:
        print("Error: no filename entered...")
        sys.exit(1)

    if (not os.path.isfile(filename)):
        print("CSV file does not exist.")
        sys.exit(1)

    try:
        image_dir = sys.argv[2]
    except:
        print("Error: no diehot image directory...")
        sys.exit(1)

    if (not os.path.isdir(image_dir)):
        print("Error: image dir DNE")
        sys.exit(1)

    output_dir = image_dir + '/scripts/'

    # initalize script text
    script_text = ''

    page = {}

    ############################################################
    # Login
    site = login()


    #  upload_file(site, '/pub/images/digcam/cat.jpg', 'cat.jpg', "hi")

    #  site.upload(open('/pub/images/digcam/cat.jpg', 'rb'), 'cat.jpg', 'hi')
    #  sys.exit()
    #######################################################
    # mk script dir

    #  if (not os.path.exists("scripts")):
        #  os.mkdir("scripts")

    #  if (not os.path.exists(output_dir)):
        #  os.mkdir(output_dir)

    #######################################################
    # Open CSV

    # arrays of dicts
    # each line a chip
    chip_array = chip_csv_file(filename)


    # initialize
    #  manufacturer = defaultdict(int)
    # 2-dinmention dict, defaultdict(int)
    #  manufacturer_family = multi_dict(2, int)
    #  manufacturer_family_chips = multi_dict(2, list) # create list of chips by manuf and family

    #  designer = defaultdict(int)

    #  trade = {}

    #  manufacturer_family_chips = defaultdict(list)

    # Loop: process each chip

    
    upload_ic = []

    test_cnt = 0

    for single_chip in chip_array:



        if test_cnt == 10 and TEST_100:
            break
        test_cnt += 1




        # Each Chip
        # create title page
        #  if not single_chip["title"] == "":
        #      title = single_chip["title"]
        #  elif not single_chip["Manufacturer"] == "" and not single_chip["Part"] == "":
        #      title = single_chip["Manufacturer"] + " - " + single_chip["Part"]
        #  else:
        #      # skip
        #      continue
        #  title = re.sub(' ', '_', title)
        #
        #  # create CHIP PAGE text
        #  (title, text) = chip_page(single_chip)
        #
        #  # write chip page
        #  if E_CHIPS:
        #      editpage(site, title, text)



        ######################
        # Creates Upload List
        if not single_chip["Logo"] == '':

           upload_ic.append( [  single_chip["Manuf"], single_chip["Fam"], single_chip["Fam2"],  single_chip["Fam3"] ,  single_chip["Logo"] ] )
        if not single_chip["Logo2"] == '':

           upload_ic.append( [  single_chip["Manuf"], single_chip["Fam"], single_chip["Fam2"],  single_chip["Fam3"] ,  single_chip["Logo2"] ] )
        if not single_chip["Logo3"] == '':

           upload_ic.append( [  single_chip["Manuf"], single_chip["Fam"], single_chip["Fam2"],  single_chip["Fam3"] ,  single_chip["Logo3"] ] )
        if not single_chip["Logo4"] == '':

           upload_ic.append( [  single_chip["Manuf"], single_chip["Fam"], single_chip["Fam2"],  single_chip["Fam3"] ,  single_chip["Logo4"] ] )
        if not single_chip["Logo5"] == '':

           upload_ic.append( [  single_chip["Manuf"], single_chip["Fam"], single_chip["Fam2"],  single_chip["Fam3"] ,  single_chip["Logo5"] ] )
        if not single_chip["Logo6"] == '':

           upload_ic.append( [  single_chip["Manuf"], single_chip["Fam"], single_chip["Fam2"],  single_chip["Fam3"] ,  single_chip["Logo6"] ] )
        if not single_chip["Logo7"] == '':

           upload_ic.append( [  single_chip["Manuf"], single_chip["Fam"], single_chip["Fam2"],  single_chip["Fam3"] ,  single_chip["Logo7"] ] )
        if not single_chip["Logo8"] == '':

           upload_ic.append( [  single_chip["Manuf"], single_chip["Fam"], single_chip["Fam2"],  single_chip["Fam3"] ,  single_chip["Logo8"] ] )



        #  chip_type["ALL"] += 1
        
    #
    # End: single_chip loop
    #########################################










    ###############################################################################
    # Page Generation
    #

    # 'Manufacturer' page, with list of manufacturer
    #  (title, text) = manufacturer_page(manufacturer)
    #  if E_MANUF:
        #  editpage(site, title, text)

    text = create_fam_logo_page(upload_ic)
    if E_LOGO:
        editpage(site, "Family logos", text)

    # upload all ic photos
    if E_UPLOAD:
        for chip_dets in upload_ic:
            # chip dets => (manuf, family, part, filename)
            if not chip_dets[4] == "": #file is listed
                upload_logo(site, image_dir, chip_dets)




    ############################################################
    ############################################################
    #############
    #############      Pages to add: 
    #############
    ############################################################
    ############################################################


    # Category:Used in workstations devices


    # FIXME, remove titles with double spaces, remove initail space




    # family pages



    #  page name ````
    #  https://happytrees.org/sites/chips-mw-1.39.0/index.php/%60%60%60%60%60

    # DNE: Category:AMCC - PowerPC family


    #  RAM (max):

    #  4G virTiB
    
    # is title mixed up with 'my lable'

    #  Introduced in 1999



    # create -> Category:Introduced in 2008 -> Chip introduction dates

    # FPU GPU DSP
    # Cetegory:No FPU]] ? should i add thisd
    #    category not created for integrated GPU, see https://happytrees.org/sites/chips-mw-1.39.0/index.php/AMD_-_AM3305DDX22GX


    # Features list: [/,] not working t=rights    
    #   https://happytrees.org/sites/chips-mw-1.39.0/index.php/ADMtek_-_ADM5106
    #   maybe split features: into feat-0, feat-1, feat-2
    #   maybe not split "/"
 #  invalid char"Category:STM32F42[79]xx family"

    #  not added integrated ...., and ..... devices
    # Seperate, Suport chip section
# End: main()








if __name__ == "__main__":
    main()
