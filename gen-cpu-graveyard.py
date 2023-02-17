#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
CHIPS - CPUU Graveyard: upload script

This script will take a CSV spreadsheet with details on files to upload


input is CSV spreadsheetfile and image dir

USAGE: python chips-pages.py [CSV_FILE] [IMAGES_DIR]

run this script in the photos dir?




columns should be

A         manufacturer
B         family
C         sub_family
D         chip_type
E         part_number
F         name (readable die name for title)
G         core_id
H         number_of_cores
I         die_size
J         image_file
K         license (should match template)
L         image_creator
M         photo_source

Columns to add maybe
    transistors
    technology
    image_creator_link
    image_type (die, layout)

A        type=row[0]
B         manufacturer=row[1]
C         family=row[2]
D         sub_family=row[3]
E         chip_type=row[4]
F         name = row[5]
G         part_number=row[6]
H         core_id=row[7]
I         number_of_cores=row[8]
J         die_size = row[9]
K        trans=row[10]
L        tech=row[11]
M        image_file=row[12]
N         license=row[13]
O         image_creator=row[14]
P         photo_source=row[15]
Q        blank [16]
R         high_res_link=row[17]
S         notes=row[18]
T         tags=row[19]
U         my_notes=row[20]


TODO
 create page [[Memory controller]]
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



############################################################################
# Config
#



#  OVERWRITE = True


userpass_location = '/home/zymos/.config/'
domain = 'happytrees.org'
urlpath = '/sites/chips-mw-1.39.0/'




# Testinge
E_CHIPS = False
E_MANUF = False
E_MANUF_FAM = False
E_CATS = True
E_UPLOAD_IC = False
E_REDIRECTS = False
E_FAMILY = False
E_STATS = False
E_TRADE = True

TEST = False
TEST_100 = False
NO_OVERWRITE_PAGE = False
NO_OVERWRITE_UPLOAD = True

E_CHIPS = True
E_MANUF = True
E_MANUF_FAM = True
E_CATS = True
#  E_UPLOAD_IC = True
#  E_REDIRECTS = True
E_FAMILY = True
E_STATS = True
#  E_TRADE = True
#  skip_lines=1


############################################################################
# Code
#

if TEST:
    E_CHIPS = False
    E_MANUF = False
    E_MANUF_FAM = False
    E_CATS = False
    E_UPLOAD_IC = False
    E_REDIRECTS = False
    E_FAMILY = False
    E_STATS = False
    E_TRADE = False




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

    (manuf, family, part, filename) = details
    
    filename_loc =  os.path.join(logo_dir, filename)
    
    #  file_out = os.path.basename(file)
    text = "{{logo-page\n|manufacturer=" + manuf + "}}"

    upload_file(site, filename_loc, filename, text)

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


    #  COP400
    #  COP444
    #  -----
    #  MCS-41
    #  MCS-48
    #  MCS-51
    #  MCS-96
    #  MCS-196
    #  MCS-251
    #  3000
    #  4004
    #  4040
    #  8008
    #  8080
    #  iAPX 432
    #  8085
    #  8086
    #  8088
    #  186
    #  188
    #  286
    #  386
    #  486
    #  486 Overdrive
    #  Pentium
    #  Pentium Mobile
    #  Pentium Pro
    #  Pentium MMX
    #  Pentium MMX Mobile
    #  Pentium Overdrive
    #  Celeron
    #  Celeron D
    #  Celeron (P6)
    #  Celeron (Netburst)
    #  Celeron (Core)
    #  Celeron (Westmere)
    #  Celeron (Sandy Bridge)
    #  Celeron (Silvermont)
    #  Celeron (Airmont)
    #  Celeron (Covington)
    #  Celeron (Mendocino)
    #  Celeron (Mendocino Mobile)
    #  Celeron (Coppermine)
    #  Celeron (Coppermine Mobile)
    #  Celeron (Northwood)
    #  Celeron (Northwood Mobile)
    #  Celeron (Tualatin)
    #  Celeron (Tualatin Mobile)
    #  Celeron (Willamette)
    #  Celeron (Northwood)
    #  Celeron (Northwood Mobile)
    #  Celeron 200-Series
    #  Celeron 900-Series Mobile
    #  Celeron (Conroe)
    #  Celeron (Bay Trail)
    #  Celeron (Braswell)
    #  Celeron (Braswell Mobile)
    #  Celeron (Apollo Lake)
    #  Celeron (Apollo Lake Mobile)
    #  Celeron (Gemini Lake)
    #  Celeron (Gemini Lake Mobile)
    #  Celeron (Elkhart Lake)
    #  Celeron (Elkhart Lake Mobile)
    #  Pentium II
    #  Pentium II Overdrive
    #  Pentium II Celeron
    #  Pentium II Mobile
    #  Pentium II (Klamath)
    #  Pentium II (Deschutes)
    #  Pentium II (Tonga)
    #  Pentium II (Dixon)
    #  Pentium III
    #  Pentium III Celeron
    #  Pentium III Xeon
    #  Pentium III Mobile
    #  Pentium III (Katmai)
    #  Pentium III (Coppermine)
    #  Pentium III (Tualatin)
    #  Pentium 4
    #  Pentium 4 (Willamette)
    #  Pentium 4 (Northwood)
    #  Pentium 4 (Gallatin)
    #  Pentium 4 (Prescott)
    #  Pentium 4 (Prescott-2M)
    #  Pentium 4 (Cedar Mill)
    #  Pentium 4 EE
    #  Pentium 4-M
    #  Pentium 4 Mobile
    #  Pentium 4 Celeron
    #  Pentium D
    #  Pentium D (Smithfield)
    #  Pentium D (Smithfield XE)
    #  Pentium D (Presler)
    #  Pentium D (Presler XE)
    #  Pentium M
    #  Pentium M (Banias)
    #  Pentium M (Dothan)
    #  Pentium Dual-Core
    #  Pentium Dual-Core (Merom-2M)
    #  Pentium Dual-Core (Allendale)
    #  Pentium Dual-Core (Wolfdale-3M)
    #  Pentium (Wolfdale-3M)
    #  Pentium (Penryn-3M)
    #  Pentium (Penryn-L)
    #  Pentium (Core)
    #  Pentium (Nehalem)
    #  Pentium (Sandy Bridge)
    #  Pentium (Ivy Bridge)
    #  Pentium (Haswell)
    #  Pentium (Broadwell)
    #  Pentium (Skylake)
    #  Pentium (Kaby Lake)
    #  Pentium (Coffee Lake)
    #  Pentium (Comet Lake)
    #  Pentium Extream Edition
    #  XEON
    #  Xeon
    #  Pentium II Xeon
    #  Pentium III Xeon
    #  Xeon (Pentium II)
    #  Xeon (Pentium II)
    #  Xeon (Netburst)
    #  Xeon (Pentium M)
    #  Xeon (Core)
    #  Xeon (Nehalem)
    #  Xeon (Sandy/Ivy Bridge)
    #  Xeon (Haswell)
    #  Xeon (Broadwell)
    #  Xeon (Skylake)
    #  Xeon (Kaby Lake)
    #  Xeon (Coffee Lake)
    #  Xeon (Comet Lake)
    #  Xeon (Cascade Lake)
    #  Xeon (Cooper Lake)
    #  Xeon (Ice Lake)
    #  Xeon (Rocket Lake)
    #  Xeon (Foster)
    #  Xeon (Prestonia)
    #  Xeon DP
    #  Xeon MP
    #  Xeon 3xxx
    #  Xeon 5xxx
    #  Xeon 6xxx
    #  Xeon 7xxx
    #  Xeon E3
    #  Xeon E5
    #  Xeon E7
    #  Xeon W
    #  Xeon Phi
    #  Itanium
    #  Itanium 2
    #  Itanium 9300
    #  Itanium 9500
    #  Itanium 9700
    #  Core
    #  Core 2
    #  Core M
    #  Core m3
    #  Core m5
    #  Core m7
    #  Core i3
    #  Core i5
    #  Core i7
    #  Core i9
    #  Core (1st Gen)
    #  Core (2nd Gen)
    #  Core (3rd Gen)
    #  Core (4th Gen)
    #  Core (5th Gen)
    #  Core (6th Gen)
    #  Core (7th Gen)
    #  Core (8th Gen)
    #  Core (9th Gen)
    #  Core (10th Gen)
    #  Core (11th Gen)
    #  Core (12th Gen)
    #  Atom (1st Gen)
    #  Atom (2nd Gen)
    #  Atom (3rd Gen)
    #  Atom (4th Gen)
    #  Atom (5th Gen)
    #  Atom (6th Gen)
    #  Atom (7th Gen)
    #  Atom (8th Gen)
    #  i860
    #  i960
    #  Polaris
    #  Cloud Computing
    #  ------
    #  5x86
    #  6x86
    #  6x86L
    #  6x86MX
    #  GX1
    #  GXm
    #  MII
    #  MXi
    #  MediaGX
    #  M3
    #  -------
    #  Nx586
    #  -------
    #  MP6
    #  -------
    #  TM5600
    #  TM5800
    #  -------
    #  WE 32100
    #  WE 32200
    #  -------
    #  DSP16
    #  DSP32
    #  -------
    #  DSP16
    #  DSP32
    #  -------
    #  MC14500
    #  6800
    #  6805
    #  6809
    #  HC05
    #  HC08
    #  HC11
    #  HC12
    #  HCS12
    #  HC16
    #  68000
    #  68020
    #  68030
    #  68040
    #  68050
    #  68060
    #  683xx
    #  PowerPC
    #  POWER
    #  POWER2
    #  POWER3
    #  POWER4
    #  POWER5
    #  POWER6
    #  POWER7
    #  POWER8
    #  POWER9
    #  POWER10
    #  POWER11
    #  POWER12
    #  z9
    #  z10
    #  z11
    #  z12
    #  z13
    #  z14
    #  z15
    #  z16
    #  z17
    #  ------
    #  WinChip
    #  WinChip 2
    #  WinChip C6
    #  -------
    #  Am5x86
    #  5k86
    #  K5
    #  K6
    #  K6-2
    #  K6-2+
    #  K6-III
    #  K6-III+
    #  K7 Athlon
    #  K7 Duron
    #  Athlon
    #  Athlon (K7)
    #  Athlon (K75)
    #  Athlon (Thunderbird)
    #  Athlon XP
    #  Athlon XP-M
    #  Athlon II
    #  Athlon II X2
    #  Athlon II X4
    #  Athlon MP
    #  Athlon X2
    #  Athlon X4
    #  Athlon 4
    #  Athlon 64
    #  Athlon 64 LE
    #  Athlon 64 FX
    #  Athlon 64 X2
    #  Athlon 64 Mobile
    #  Athlon Neo
    #  Athlon Neo X2
    #  Athlon (K8)
    #  Athlon (K10)
    #  Athlon (Piledriver)
    #  Athlon (Jaguar)
    #  Athlon (Steamroller)
    #  Athlon (Excavator)
    #  Athlon (Zen)
    #  Duron
    #  Duron Mobile
    #  Duron (Spitfire)
    #  Duron (Morgan)
    #  Duron (Applebred)
    #  Duron Mobile (Spitfire)
    #  Duron Mobile (Camaro)
    #  Sempron
    #  Sempron 64
    #  Sempron LE
    #  Sempron X2
    #  Sempron Mobile
    #  Sempron 2xxx
    #  Sempron 3xxx
    #  Sempron 1xx
    #  Sempron 2xx
    #  Sempron SI
    #  Semprom 2xxU
    #  Semprom M1xx
    #  E1-Series
    #  E2-Series
    #  Opteron
    #  Opteron 3xxx
    #  Opteron 4xxx
    #  Opteron 6xxx
    #  Opteron X
    #  Opteron A
    #  Opteron (K8)
    #  Opteron (K10)
    #  Opteron (Bulldozer)
    #  Opteron (Pildriver)
    #  Opteron (Excavator)
    #  Opteron (Jaguar)
    #  Opteron (ARM)
    #  Phenom
    #  Phenom II
    #  Phenom X3
    #  Phenom X4
    #  Turion
    #  Turion 64
    #  Turion ML
    #  Turion 64 X2
    #  Turion X2
    #  Turion X2 Ultra
    #  Turion II
    #  Turion II Ultra
    #  Turion II Neo
    #  Turion Neo
    #  Turion Neo X2
    #  G-Series
    #  R-Series
    #  V-Series
    #  Ryzen
    #  Rysen 3
    #  Sysen 5
    #  Rysen 7
    #  A4-Series
    #  A6-Series
    #  A8-Series
    #  A9-Series
    #  A10-Series
    #  A12-Series
    #  FirePro
    #  FX-Series
    #  Zen
    #  Zen+
    #  Zen 2
    #  Zen 3
    #  Threadripper
    #  Threadripper Pro
    #  Epyc
    #  --------
    #  Cyrix III
    #  C3
    #  Eden
    #  Eden ESP
    #  C7
    #  C7-M
    #  C7-D
    #  Nano
    #  Nano X2
    #  CHA
    #  --------
    #  Alpha
    #  Alpha AXP
    #  --------
    #  V20
    #  V25
    #  V30
    #  V50
    #  V60
    #  -------
    #  R2000
    #  R3000
    #  R6000
    #  R4000
    #  R4200
    #  R4300i
    #  R4400
    #  R4600
    #  R4700
    #  R5000
    #  RM5271
    #  RM7000
    #  R8000
    #  R10000
    #  R12000
    #  MIPS32
    #  --------
    #  H1
    #  H2
    #  ---------
    #  SPARC
    #  SuperSPARC
    #  SuperSPARC II
    #  TurboSPARC
    #  hyperSPARC
    #  microSPARC
    #  microSPARC II
    #  UltraSPARC
    #  UltraSPARC II
    #  UltraSPARC III
    #  UltraSPARC IV
    #  SPARC T1
    #  SPARC T2
    #  SPARC RK
    #  SPARC T3
    #  SPARC T4
    #  SPARC T5
    #  SPARC M5
    #  SPARC M6
    #  SPARC M7
    #  SPARC S7
    #  SPARC M7
    #  SPARC M8
    #  LEON
    #  LEON2
    #  LEON3
    #  LEON4
    #  LEON5
    #  LEON6
    #  SPARClite
    #  SPARC64
    #  SPARC64 II
    #  SPARC64 III
    #  SPARC64 GP
    #  SPARC64 IV
    #  SPARC64 V
    #  SPARC64 VI
    #  SPARC64 VII
    #  SPARC64 VIII
    #  SPARC64 X
    #  SPARC64 XI
    #  SPARC64 XII
    #  SPARC 900
    #  R1000
    #  ---------
    #  PA RISC
    #  PowerVR2
    #  SuperH
    #  SH-1
    #  SH-2
    #  SH-3
    #  SH-4
    #  ------
    #  Z80
    #  Z8
    #  Z8000
    #  Z180
    #  -------
    #  6502
    #  65816
    #  65C816
    #  -------
    #  Game & Watch
    #  Game Boy
    #  Game Goy Color
    #  Game Boy Advanced
    #  Nintendo DS
    #  Nintendo 3DS
    #  Nintendo Switch
    #  Nintendo
    #  NES
    #  Super Nintendo
    #  SNES
    #  Nintendo 64
    #  N64
    #  Game Cube
    #  Wii
    #  Wii U
    #  -------
    #  Xbox
    #  Xbox 360
    #  Xbox One
    #  Xbox One X
    #  Xbox Series X/S
    #  -------
    #  Playstation I
    #  Playstation II
    #  Playstation III
    #  Playstation 4
    #  Playstation 5
    #  -------
    #  CXP80300
    #  CXP80600
    #  -------
    #  PIC10
    #  PIC12
    #  PIC16
    #  PIC18
    #  PIC24
    #  PIC32
    #  dsPIC
    #  -------
    #  NS32000
    #  NS16000
    #  -------
    #  TMS1000
    #  TMS7000
    #  TMS9900
    #  TMS320
    #  -------
    #  TV/Monitor




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
                    if (entry == "New"):
                        New_line = col
                    elif (entry == "title"):
                        title_line = col
                    elif (entry == "owned"):
                        owned_line = col
                    elif (entry == "Trade"):
                        Trade_line = col
                    elif (entry == "Manufacturer"):
                        Manufacturer_line = col
                    elif (entry == "Part"):
                        Part_line = col
                    elif (entry == "Label ID"):
                        Label_ID_line = col
                    elif (entry == "Alt ID 1"):
                        Alt_ID_1_line = col
                    elif (entry == "Alt ID 2"):
                        Alt_ID_2_line = col
                    elif (entry == "Alt ID 3"):
                        Alt_ID_3_line = col
                    elif (entry == "Type"):
                        Type_line = col
                    elif (entry == "Family"):
                        Family_line = col
                    elif (entry == "Sub-Family"):
                        Sub_Family_line = col
                    elif (entry == "sub-family2"):
                        sub_family2_line = col
                    elif (entry == "sub-family3"):
                        sub_family3_line = col
                    elif (entry == "Core"):
                        Core_line = col
                    elif (entry == "CPUID"):
                        CPUID_line = col
                    elif (entry == "Instruction set"):
                        Instruction_set_line = col
                    elif (entry == "IS Ext"):
                        IS_Ext_line = col
                    elif (entry == "Instruction link"):
                        Instruction_link_line = col
                    elif (entry == "Computer architecture"):
                        Computer_architecture_line = col
                    elif (entry == "ISA"):
                        ISA_line = col
                    elif (entry == "Microarchitecture"):
                        Microarchitecture_line = col
                    elif (entry == "Designer of Core"):
                        Designer_of_Core_line = col
                    elif (entry == "Clone"):
                        Clone_line = col
                    elif (entry == "Cores"):
                        Cores_line = col
                    elif (entry == "Pipeline"):
                        Pipeline_line = col
                    elif (entry == "Multiprocessing"):
                        Multiprocessing_line = col
                    elif (entry == "Architecture"):
                        Architecture_line = col
                    elif (entry == "Bus Width"):
                        Bus_Width_line = col
                    elif (entry == "Address Width"):
                        Address_Width_line = col
                    elif (entry == "Speed"):
                        Speed_line = col
                    elif (entry == "Bus speed"):
                        Bus_speed_line = col
                    elif (entry == "Bus type"):
                        Bus_type_line = col
                    elif (entry == "Clock multiplier"):
                        Clock_multiplier_line = col
                    elif (entry == "FPU"):
                        FPU_line = col
                    elif (entry == "GPU"):
                        GPU_line = col
                    elif (entry == "DSP"):
                        DSP_line = col
                    elif (entry == "L1 cache"):
                        L1_cache_line = col
                    elif (entry == "L1 shared"):
                        L1_shared_line = col
                    elif (entry == "L1 data"):
                        L1_data_line = col
                    elif (entry == "L1 instruction"):
                        L1_instruction_line = col
                    elif (entry == "L2 cache"):
                        L2_cache_line = col
                    elif (entry == "L3 cache"):
                        L3_cache_line = col
                    elif (entry == "ROM Int"):
                        ROM_Int_line = col
                    elif (entry == "ROM type"):
                        ROM_type_line = col
                    elif (entry == "RAM Int"):
                        RAM_Int_line = col
                    elif (entry == "RAM Max"):
                        RAM_Max_line = col
                    elif (entry == "RAM type"):
                        RAM_type_line = col
                    elif (entry == "Package"):
                        Package_line = col
                    elif (entry == "Package Size"):
                        Package_Size_line = col
                    elif (entry == "Socket"):
                        Socket_line = col
                    elif (entry == "Transistors"):
                        Transistors_line = col
                    elif (entry == "Process Size"):
                        Process_Size_line = col
                    elif (entry == "Technology"):
                        Technology_line = col
                    elif (entry == "Die Size"):
                        Die_Size_line = col
                    elif (entry == "Vcc"):
                        Vcc_line = col
                    elif (entry == "Vcc range"):
                        Vcc_range_line = col
                    elif (entry == "Vcore"):
                        Vcore_line = col
                    elif (entry == "Vcc (I/O)"):
                        Vcc__I_O__line = col
                    elif (entry == "V(I/O) secondary"):
                        V_I_O__secondary_line = col
                    elif (entry == "V(I/O) tertiary"):
                        V_I_O__tertiary_line = col
                    elif (entry == "Power min"):
                        Power_min_line = col
                    elif (entry == "Power typ"):
                        Power_typ_line = col
                    elif (entry == "Power max"):
                        Power_max_line = col
                    elif (entry == "TDP"):
                        TDP_line = col
                    elif (entry == "Low power modes"):
                        Low_power_modes_line = col
                    elif (entry == "Grade"):
                        Grade_line = col
                    elif (entry == "Date Introduced"):
                        Date_Introduced_line = col
                    elif (entry == "Year"):
                        Year_line = col
                    elif (entry == "Initial price"):
                        Initial_price_line = col
                    elif (entry == "Applications"):
                        Applications_line = col
                    elif (entry == "Features"):
                        Features_line = col
                    elif (entry == "Rarity"):
                        Rarity_line = col
                    elif (entry == "Description"):
                        Description_line = col
                    elif (entry == "Photo 1"):
                        Photo_1_line = col
                    elif (entry == "Photo 2"):
                        Photo_2_line = col
                    elif (entry == "Photo 3"):
                        Photo_3_line = col
                    elif (entry == "Photo 4"):
                        Photo_4_line = col
                    elif (entry == "Photo 5"):
                        Photo_5_line = col
                    elif (entry == "Photo die"):
                        Photo_die_line = col
                    elif (entry == "Photo die license"):
                        Photo_die_license_line = col
                    elif (entry == "Datasheet"):
                        Datasheet_line = col
                    elif (entry == "Reference 1"):
                        Reference_1_line = col
                    elif (entry == "Reference 2"):
                        Reference_2_line = col
                    elif (entry == "Reference 3"):
                        Reference_3_line = col
                    elif (entry == "Reference 4"):
                        Reference_4_line = col
                    elif (entry == "Reference 5"):
                        Reference_5_line = col
                    col += 1
            # end detect the column

            # add new chip to array
            else:
                chip_data.append({"New": row[New_line],
                                  "title": row[title_line],
                                  "owned": row[owned_line],
                                  "Trade": row[Trade_line],
                                  "Manufacturer": row[Manufacturer_line],
                                  "Part": row[Part_line],
                                  "Label_ID": row[Label_ID_line],
                                  "Alt_ID_1": row[Alt_ID_1_line],
                                  "Alt_ID_2": row[Alt_ID_2_line],
                                  "Alt_ID_3": row[Alt_ID_3_line],
                                  "Type": row[Type_line],
                                  "Family": row[Family_line],
                                  "Sub_Family": row[Sub_Family_line],
                                  "sub_family2": row[sub_family2_line],
                                  "sub_family3": row[sub_family3_line],
                                  "Core": row[Core_line],
                                  "CPUID": row[CPUID_line],
                                  "Instruction_set": row[Instruction_set_line],
                                  "IS_Ext": row[IS_Ext_line],
                                  "Instruction_link": row[Instruction_link_line],
                                  "Computer_architecture": row[Computer_architecture_line],
                                  "ISA": row[ISA_line],
                                  "Microarchitecture": row[Microarchitecture_line],
                                  "Designer_of_Core": row[Designer_of_Core_line],
                                  "Clone": row[Clone_line],
                                  "Cores": row[Cores_line],
                                  "Pipeline": row[Pipeline_line],
                                  "Multiprocessing": row[Multiprocessing_line],
                                  "Architecture": row[Architecture_line],
                                  "Bus_Width": row[Bus_Width_line],
                                  "Address_Width": row[Address_Width_line],
                                  "Speed": row[Speed_line],
                                  "Bus_speed": row[Bus_speed_line],
                                  "Bus_type": row[Bus_type_line],
                                  "Clock_multiplier": row[Clock_multiplier_line],
                                  "FPU": row[FPU_line],
                                  "GPU": row[GPU_line],
                                  "DSP": row[DSP_line],
                                  "L1_cache": row[L1_cache_line],
                                  "L1_shared": row[L1_shared_line],
                                  "L1_data": row[L1_data_line],
                                  "L1_instruction": row[L1_instruction_line],
                                  "L2_cache": row[L2_cache_line],
                                  "L3_cache": row[L3_cache_line],
                                  "ROM_Int": row[ROM_Int_line],
                                  "ROM_type": row[ROM_type_line],
                                  "RAM_Int": row[RAM_Int_line],
                                  "RAM_Max": row[RAM_Max_line],
                                  "RAM_type": row[RAM_type_line],
                                  "Package": row[Package_line],
                                  "Package_Size": row[Package_Size_line],
                                  "Socket": row[Socket_line],
                                  "Transistors": row[Transistors_line],
                                  "Process_Size": row[Process_Size_line],
                                  "Technology": row[Technology_line],
                                  "Die_Size": row[Die_Size_line],
                                  "Vcc": row[Vcc_line],
                                  "Vcc_range": row[Vcc_range_line],
                                  "Vcore": row[Vcore_line],
                                  "Vcc__I_O_": row[Vcc__I_O__line],
                                  "V_I_O__secondary": row[V_I_O__secondary_line],
                                  "V_I_O__tertiary": row[V_I_O__tertiary_line],
                                  "Power_min": row[Power_min_line],
                                  "Power_typ": row[Power_typ_line],
                                  "Power_max": row[Power_max_line],
                                  "TDP": row[TDP_line],
                                  "Low_power_modes": row[Low_power_modes_line],
                                  "Grade": row[Grade_line],
                                  "Date_Introduced": row[Date_Introduced_line],
                                  "Year": row[Year_line],
                                  "Initial_price": row[Initial_price_line],
                                  "Applications": row[Applications_line],
                                  "Features": row[Features_line],
                                  "Rarity": row[Rarity_line],
                                  "Description": row[Description_line],
                                  "Photo_1": row[Photo_1_line],
                                  "Photo_2": row[Photo_2_line],
                                  "Photo_3": row[Photo_3_line],
                                  "Photo_4": row[Photo_4_line],
                                  "Photo_5": row[Photo_5_line],
                                  "Photo_die": row[Photo_die_line],
                                  "Photo_die_license": row[Photo_die_license_line],
                                  "Datasheet": row[Datasheet_line],
                                  "Reference_1": row[Reference_1_line],
                                  "Reference_2": row[Reference_2_line],
                                  "Reference_3": row[Reference_3_line],
                                  "Reference_4": row[Reference_4_line],
                                  "Reference_5": row[Reference_5_line]})
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


    # Applications
    #  chip_single["Applications"]
    #  apps = re.split(',', chip_single["Applications"])
    #  app_string = ''
    #  app_cats = ''
    #  for app in apps:
    #      apps_string += '[[:category:Used in ' + app + 'devices|' + app + ']], '
    #      app_cats += '[[category:used in ' + app ' devices]]'



    # Integrated
    #  chip_single["Features"]
        #  apps_string += '[[:category:integrated ' + app + '|' + app + ']], '
        #  app_cats += '[[category:integrated ' + app ']]'

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


    # exit if ...
    if unit == 'length' and re.findall(r'Cu$', value):
        return value


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

    if (not os.path.exists("scripts")):
        os.mkdir("scripts")

    if (not os.path.exists(output_dir)):
        os.mkdir(output_dir)

    #######################################################
    # Open CSV

    # arrays of dicts
    # each line a chip
    chip_array = chip_csv_file(filename)

    # KEYS
    #  "New"
    #  "title"
    #  "owned"
    #  "Trade"
    #  "Manufacturer"
    #  "Part"
    #  "Label_ID"
    #  "Alt_ID_1"
    #  "Alt_ID_2"
    #  "Alt_ID_3"
    #  "Type"
    #  "Family"
    #  "Sub_Family"
    #  "sub_family2"
    #  "sub_family3"
    #  "Core"
    #  "CPUID"
    #  "Instruction_set"
    #  "IS_Ext"
    #  "Instruction_link"
    #  "Computer_architecture"
    #  "ISA"
    #  "Microarchitecture"
    #  "Designer_of_Core"
    #  "Clone"
    #  "Cores"
    #  "Pipeline"
    #  "Multiprocessing"
    #  "Architecture"
    #  "Bus_Width"
    #  "Address_Width"
    #  "Speed"
    #  "Bus_speed"
    #  "Bus_type"
    #  "Clock_multiplier"
    #  "FPU"
    #  "GPU"
    #  "DSP"
    #  "L1_cache"
    #  "L1_shared"
    #  "L1_data"
    #  "L1_instruction"
    #  "L2_cache"
    #  "L3_cache"
    #  "ROM_Int"
    #  "ROM_type"
    #  "RAM_Int"
    #  "RAM_Max"
    #  "RAM_type"
    #  "Package"
    #  "Package_Size"
    #  "Socket"
    #  "Transistors"
    #  "Process_Size"
    #  "Technology"
    #  "Die_Size"
    #  "Vcc"
    #  "Vcc_range"
    #  "Vcore"
    #  "Vcc__I_O_"
    #  "V_I_O__secondary"
    #  "V_I_O__tertiary"
    #  "Power_min"
    #  "Power_typ"
    #  "Power_max"
    #  "TDP"
    #  "Low_power_modes"
    #  "Grade"
    #  "Date_Introduced"
    #  "Year"
    #  "Initial_price"
    #  "Applications"
    #  "Features"
    #  "Rarity"
    #  "Description"
    #  "Photo_1"
    #  "Photo_2"
    #  "Photo_3"
    #  "Photo_4"
    #  "Photo_5"
    #  "Photo_die"
    #  "Photo_die_license"
    #  "Datasheet"
    #  "Reference_1"
    #  "Reference_2"
    #  "Reference_3"
    #  "Reference_4"

    # initialize
    manufacturer = defaultdict(int)
    # 2-dinmention dict, defaultdict(int)
    manufacturer_family = multi_dict(2, int)
    #  manufacturer_family_chips = multi_dict(2, list) # create list of chips by manuf and family

    designer = defaultdict(int)
    application = defaultdict(int)
    chip_type = defaultdict(int)
    chip_type_count = defaultdict(int)
    introduction_date = defaultdict(int)
    bit_width = defaultdict(int)
    architecture = defaultdict(int)
    ISA = defaultdict(int)
    micro_arch = defaultdict(int)
    core_name = defaultdict(int)
    cores = defaultdict(int)
    fpu_type = defaultdict(int)
    technology = defaultdict(int)
    process = defaultdict(int)
    package = defaultdict(int)
    speed = defaultdict(int)
    family = defaultdict(int)
    family_count = defaultdict(int)
    sub_families = defaultdict(int)
    integrated_components = defaultdict(int)
    taged_cats = defaultdict(int)

    trade = {}

    manufacturer_family_chips = defaultdict(list)

    # Loop: process each chip

    
    upload_ic = []
    redirects = {}
    family_chips = defaultdict(list)

    test_cnt = 0

    for single_chip in chip_array:



        if test_cnt == 100 and TEST_100:
            break
        test_cnt += 1




        # Each Chip
        # create title page
        if not single_chip["title"] == "":
            title = single_chip["title"]
        elif not single_chip["Manufacturer"] == "" and not single_chip["Part"] == "":
            title = single_chip["Manufacturer"] + " - " + single_chip["Part"]
        else:
            # skip
            continue
        title = re.sub(' ', '_', title)

        # create CHIP PAGE text
        (title, text) = chip_page(single_chip)

        # write chip page
        if E_CHIPS:
            editpage(site, title, text)



        # Manufacturer
        # inc counts
        if not is_na(single_chip["Manufacturer"]):
            manufacturer[single_chip["Manufacturer"]] += 1

        if not (is_na(single_chip["Manufacturer"]) or is_na(single_chip["Manufacturer"])):
            manufacturer_family[single_chip["Manufacturer"]
                            ][single_chip["Family"]] += 1

        # list of chips foreach "Manufacturer - Family"
        #  manufacturer_family_chips[single_chip["Manufacturer"] + " - " + single_chip["Family"]] = title
        #  manufacturer_family_chips[single_chip["Manufacturer"] + " - " + single_chip["Family"]].append(title)
        # store manuf, family, and chip name(title)
        #  manufacturer_family_chips[single_chip["Manufacturer"]][single_chip["Family"]].append( [single_chip["Manufacturer"], single_chip["Family"], title] )



        # Manuf-Family
        if single_chip["Family"] == '':
            manufacturer_family_chips[single_chip["Manufacturer"] + 
                                " - other"].append([single_chip["Manufacturer"], "other", title])
        else:
            manufacturer_family_chips[single_chip["Manufacturer"] + " - " + single_chip["Family"] +
                                " family"].append([single_chip["Manufacturer"], single_chip["Family"], title])
            

        # Family pages
        if not is_na(single_chip["Family"]):
            family[single_chip["Family"]] += 1 # list of families with counts
            family_chips[single_chip["Family"]].append(title)
            



        # Designer
        if not is_na(single_chip["Designer_of_Core"]):
            designer[single_chip["Designer_of_Core"]] += 1



        # Apps: splits list of apps
        for app in re.split(r"[,\/]", single_chip["Applications"]):
            #  print(app)
            if not is_na(single_chip["Applications"]):
                application[app] += 1



        # Types
        if not is_na(single_chip["Type"]):
             chip_type[single_chip["Type"]] += 1



        # Year: removes any years that dont make sence
        if not is_na(single_chip["Year"]):
            year = single_chip["Year"]
            if isinstance(year, int) and year > 1800 and year < 2099:
                introduction_date[str(year)] += 1
            else:
                #  print("string")
                try:
                    year_int = int(year)
                    if year_int > 1800 and year_int < 2099:
                        introduction_date[str(year_int)] += 1
                except ValueError:
                    introduction_date[str(year)] += 1
            #  try:
                #  int(year)
                #  print("Syntax error: Year=" + year)


        # create, counts, 
        if not is_na(single_chip["Bus_Width"]):
            bit_width[unit_fix(single_chip["Bus_Width"], "bit")] += 1
        if not is_na(single_chip["Computer_architecture"]):
            architecture[single_chip["Computer_architecture"]] += 1
        if not is_na(single_chip["ISA"]):
            ISA[single_chip["ISA"]] += 1
        if not is_na(single_chip["Microarchitecture"]):
            micro_arch[single_chip["Microarchitecture"]] += 1
        if not is_na(single_chip["Core"]):
            core_name[single_chip["Core"]] += 1
        if not is_na(single_chip["Cores"]):
            cores[single_chip["Cores"]] += 1
        if not is_na(single_chip["FPU"]):
            fpu_type[single_chip["FPU"]] += 1
        if not is_na(single_chip["Technology"]):
            technology[single_chip["Technology"]] += 1
        if not is_na(single_chip["Process_Size"]):
            process[unit_fix(single_chip["Process_Size"], "length")] += 1
        if not is_na(single_chip["Package"]):
            package[single_chip["Package"]] += 1

        if not is_na(single_chip["Speed"]):
            speed[unit_fix(single_chip["Speed"], "frequency")] += 1
        #  print(single_chip["Speed"])
        #  if not is_na(single_chip["Family"]):
            #  family[single_chip["Family"]] += 1
        if not is_na(single_chip["Sub_Family"]):
            sub_families[single_chip["Sub_Family"]] += 1
        if not is_na(single_chip["sub_family2"]):
            sub_families[single_chip["sub_family2"]] += 1
        if not is_na(single_chip["sub_family3"]):
            sub_families[single_chip["sub_family3"]] += 1


        ###########################
        # Integrated Components: splits list of components
        for feat in re.split(r"[,]", single_chip["Features"]):
            feat = re.sub(r"^\s*", '', feat)
            if not is_na(single_chip["Features"]):
                if not feat == '':
                    integrated_components[feat] += 1


        ######################
        # Trade 
        if str.isdigit(single_chip["Trade"]):
            trade[title] = single_chip["Trade"]


        ######################
        # Creates Upload List
        upload_ic.append( [  single_chip["Manufacturer"], single_chip["Family"], single_chip["Part"],  single_chip["Photo_1"] ] )


        ##################
        # Redircts
        #
        # legacy redirects
        #  https://happytrees.org/chips/ic/AMD/AM2901DC
        #  https://happytrees.org/chips/mf/AMD/Am5x86
        #  https://happytrees.org/chips/mf/Fujitsu/All
        #  https://happytrees.org/chips/m/AMD
        #  https://happytrees.org/chips/m/Others
        #  https://happytrees.org/chips/families/
        #  https://happytrees.org/chips/family/1802
        #  https://happytrees.org/chips/boards/
        #  https://happytrees.org/chips/module_boards/
        #  https://happytrees.org/chips/board/Sun/501_3041
        #  https://happytrees.org/chips/categories/
        #  https://happytrees.org/chips/trade/
        #  https://happytrees.org/chips/glossary/
        #  https://happytrees.org/chips/sitemap/
        #  https://happytrees.org/chips/release_date/
        #  https://happytrees.org/chips/logos/
        #
        #  https://happytrees.org/chips/architecture/
        #  https://happytrees.org/chips/chip_types/
        #  https://happytrees.org/chips/ISA/
        #  https://happytrees.org/chips/release_date/
        #  https://happytrees.org/chips/technologies/
        #  https://happytrees.org/chips/data_width/
        #  https://happytrees.org/chips/applications/
        #  https://happytrees.org/chips/families/
        #  https://happytrees.org/chips/manufacturers/

        # single chip redirec
        if single_chip["Manufacturer"] == "AT&T":
            n_manuf = "ATT"
        else:
            n_manuf = re.sub(r"[^a-zA-Z0-9]", "_", single_chip["Manufacturer"])
        n_part = re.sub(r"[^a-zA-Z0-9]", "_", single_chip["Part"])
        n_fam = re.sub(r"[^a-zA-Z0-9]", "_", single_chip["Family"])
        if not single_chip["title"] == '' and  not single_chip["Manufacturer"] == ""  and not single_chip["Part"] == "":
            redirects[single_chip["title"]] = "ic/" + n_manuf + "/" + n_part
        elif not single_chip["Manufacturer"] == ""  and not single_chip["Part"] == "":
            redirects[single_chip["Manufacturer"] + " - " + single_chip["Part"]] = "ic/" + n_manuf + "/" + n_part
        # manufacturer redirect
        if not single_chip["Manufacturer"] == "":
            redirects[single_chip["Manufacturer"]] = "m/" + n_manuf
        # family redirect
        if not single_chip["Family"] =="":
            redirects[single_chip["Family"] + " family"] = "family/" + n_fam
        # manuf-family rediects
        if not single_chip["Manufacturer"] == "" and not single_chip["Family"] =="":
            redirects[single_chip["Manufacturer"] + " - " + single_chip["Family"] + ' family'] = "mf/" + n_manuf + "/" + n_fam


        chip_type["ALL"] += 1 
        
    #
    # End: single_chip loop
    #########################################








    #  pprint("s")
    #  pprint(chip_type)
    #  pprint(year)
    #  pprint(introduction_date)
    #  pprint(bit_width)
    #  pprint(architecture)
    #  pprint(ISA)
    #  pprint(micro_arch)
    #  pprint(core_name)
    #  pprint(cores)
    #  pprint(fpu_type)
    #  pprint(technology)
    #  pprint(process)
    #  pprint(package)
    #  pprint(speed)
    #  pprint(family)
    #  pprint(sub_families)
    #  pprint(integrated_components)


    ###############################################################################
    # Page Generation
    #

    # 'Manufacturer' page, with list of manufacturer
    (title, text) = manufacturer_page(manufacturer)
    if E_MANUF:
        editpage(site, title, text)

    # Manufacturer pages with list of families
    #  print(manufacturer_family.items())
    for manuf in manufacturer_family:
        (title, text) = all_manufacturer_pages(manuf, manufacturer_family)
        if E_MANUF:
            editpage(site, title, text)

    # Manufacturer - Family pages with list of chips
    #  for (manuf, family, chip_list) in manufacturer_family_chips:
        #  (title, text) = manufacturer_family_pages(manuf, family, chip_list)
    #  for manufacturer_family_chips_list in manufacturer_family_chips.keys():
        #  for manufacturer_family_chips_list_list in manufacturer_family_chips[manufacturer_family_chips_list].keys():
        #  pprint(manufacturer_family_chips[manufacturer_family_chips_list_list])
    #           pprint(manufacturer_family_chips_list_list)
    # x

    # Manufacturer-Family pages with links to chips
    for manufacturer_family_chips_list in manufacturer_family_chips:
        #  pprint("--------------")
        #  print(manufacturer_family_chips_list)
        #  pprint(manufacturer_family_chips[manufacturer_family_chips_list])
        (title, text) = manufacturer_family_pages(manufacturer_family_chips_list,
                                                  manufacturer_family_chips[manufacturer_family_chips_list])
        if E_MANUF_FAM:
            editpage(site, title, text)



    # Families
    for fam in family.keys():
        (title, text) = family_pages(fam, family[fam], family_chips[fam]) # family name, count, [manuf_list, title]
        if E_FAMILY:
            editpage(site, title, text)
        #  family[single_chip["Family"]] += 1 # list of families with counts
        #  family_chips[single_chip["Family"]].append(title)
 

    


    # Statistics
    for ty in ("ALL", "CPU","MCU", "SoC", "BSP", "FPU", "Support"):
        title = "Template:stats/" + ty
        text = chip_type[ty]
        if E_STATS:
            editpage(site, title, text)


    # Trade list (automated)
    title = "Template:trade_list/list"
    text = "{{trade_list\n"
    x = 0
    for trd in trade.keys():
        text += "| chip-" + str(x) + " = " + trd + "\n"
        text += "| trade-cnt-" + str(x) + " = " + trade[trd] + "\n"
        x += 1
    text += "}}"
    if E_TRADE:
        editpage(site, title, text)


    # Categories

    # [[category:MANUF - FAM family]]

    if E_CATS:
        for manuf in manufacturer_family.keys():
            for fam in manufacturer_family[manuf].keys():
                if fam == '':
                    title = "Category:" + manuf + " - other"
                    text = "[[Category:" + manuf + "]][[Category:tags]]"
                else:
                    title = "Category:" + manuf + " - " + fam + " family"
                    text = "[[Category:" + manuf + "]][[category:" + fam + "]][[Category:tags]]"
                editpage(site, title, text)

        for element in designer:
            if not element == '':
                title = "Category:Designed by " + element
                text = "[[Category:Core designer]][[Category:tags]]"
                editpage(site, title, text)

        for element in application:
            if not element == "":
                title = "Category:Used in " + element + " devices"
                text = "[[Category:Application]][[Category:tags]]"
                editpage(site, title, text)

        for element in chip_type:
            if not element == "":
                title = "Category:" + element
                text = "[[Category:Chip types]][[Category:tags]]"
                editpage(site, title, text)

        for element in introduction_date:
            if not element == "":
                title = "Category:introduced in " + str(element)
                text = "[[Category:Date]][[Category:tags]]"
                editpage(site, title, text)

        for element in bit_width:
            if not element == "":
                title = "Category:" + unit_fix(element, "bit")
                text = "[[Category:Bit-width]][[Category:tags]]"
                print(title)
                # FIXME: 'Category:3-bit' crashes
                editpage(site, title, text)

        for element in architecture:
            if not element == "":
                title = "Category:" + element + " architecture"
                text = "[[Category:Architecture]][[Category:tags]]"
                editpage(site, title, text)

        for element in ISA:
            if not element == "":
                title = "Category:" + element + " ISA"
                text = "[[Category:ISA]][[Category:tags]]"
                editpage(site, title, text)

        for element in micro_arch:
            if not element == "":
                title = "Category:" + element +  " µarch"
                text = "[[Category:Micro-architecture]][[Category:tags]]"
                editpage(site, title, text)

        for element in core_name:
            if not element == "":
                title = "Category:" + element + " core"
                text = "[[Category:Core ID]][[Category:tags]]"
                editpage(site, title, text)

        for element in cores:
            if not element == "":
                title = "Category:" + str(element) + " cores"
                text = "[[Category:Number of cores]][[Category:tags]]"
                editpage(site, title, text)

        for element in fpu_type:
            if not element == "":
                title = "Category:" + element + " FPU"
                text = "[[Category:FPU]][[Category:tags]]"
                editpage(site, title, text)

        for element in technology:
            if not element == "":
                title = "Category:" + element + " technology"
                text = "[[Category:Technology]][[Category:tags]]"
                editpage(site, title, text)

        for element in process:
            if not element == "":
                title = "Category:" + element + " process"
                text = "[[Category:manufacturing process]][[Category:tags]]"
                editpage(site, title, text)

        for element in package:
            if not element == "":
                title = "Category:" + element + " package"
                text = "[[Category:Package]][[Category:tags]]"
                editpage(site, title, text)

        for element in speed:
            if not element == "":
                title = "Category:" + element
                text = "[[Category:Speed]][[Category:tags]]"
                editpage(site, title, text)

        for element in family:
            if not element == "":
                title = "Category:" + element + " family"
                text = "[[Category:Family]][[Category:tags]]"
                editpage(site, title, text)

        for element in sub_families:
            if not element == "":
                title = "Category:" + element + " family"
                text = "[[Category:Sub-family]][[Category:tags]]"
                editpage(site, title, text)
    #
        for element in integrated_components:
            if not element == "":
                title = "Category:Integrated " + element
                text = "[[Category:integrated components]][[Category:tags]]"
                editpage(site, title, text)
        # End: if E_CATS

        # Category for categories

        text = "[[Category:Categories]]"
        title = "Category:Core designer"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Application"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Chip types"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Date"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Bit-width"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Architecture"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:ISA"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Micro-architecture"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Core ID"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Number of cores"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:FPU"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Technology"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:manufacturing process"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Package"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Speed"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Family"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:Sub-family"
        editpage(site, title, text)

        text = "[[Category:Categories]]"
        title = "Category:integrated components"
        editpage(site, title, text)





    # upload all ic photos
    if E_UPLOAD_IC:
        for chip_dets in upload_ic:
            # chip dets => (manuf, family, part, filename)
            if not chip_dets[3] == "": #file is listed
                upload_chip(site, image_dir, chip_dets)



    # Create Redirects
    for page in redirects.keys():
        title = redirects[page]
        text = "#REDIRECT [[" + page + "]]"
        if E_REDIRECTS:
            editpage(site, title, text)





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

#  NA cores


#  Category:Intel - NA family






#  Data-bus (ext):
#
#  NA-bit
#
#  Address-bus:
#
#  NA-bit

#  FPU / GPU: Integrated / no        (No GPU is showing and cat)


#  Transistors: 153.8M

    # Missing: File:Ic-photo-TI--TMS70C02NL--(TMS7000-MCU).JPG
#  File:Ic-photo-AMD--AM2901CPC-(Am2900-ALU).png
#  File:Ic-photo-AMD--AM2960DC-(Am2900).png


#  -----------
#  family category
#  Category:WSI - Am2900 family, shows 'Categories:    WSIAm2900Tags'

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
