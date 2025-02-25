from collections import namedtuple

from tasks.get_drive_info import get_drive_info
import logging
import logs


LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)

# From top to bottom, Brand, SN, size
#
# Bay number 1:
# - WD, 3WK2UM2J, 18TB
# - TSBA, 62X0A0FNFJDH, 18TB
# - TSBA, Z130A0ASFJDH, 18TB
# - SEA, ZLW226D6, 12TB
# - TSBA, 62X0A01SFJDH, 18TB
# - TSBA, 62P0A269FJDH, 18TB
# - TSBA, 91T0A20HFVGG, 16TB
# - TSBA, Y1S0A091FJDH, 18TB
#
# Bay number 2:
# - WD, 3GG8GH4E, 18TB
# - TSBA, 91T0A1YFFVGG, 16TB
# - SEA, ZL2DJJKF, 14TB
# - SEA, ZA2DTK2E, 10TB
# - SEA, ZL2EBHZY, 16TB
# - SEA, ZL2GDWF1, 16TB
# - SEA, ZL2E79D9, 14TB
# - TSBA, Z130A09JFJDH, 18TB
#
#
# Bay number 4:
# - TSBA, Y1Q0A09JFJDH, 18TB
# - WD, 3WJ87UJK, 18TB
# - TSBA, Y1Q0A0EBFJDH, 18TB
# - SEA, ZL29EZD1, 14TB
# - TSBA, Y1R0A1V0FJDH, 18TB
# - SEA, ZA2DNLBY, 10TB
# - SEA, ZLW28R8M, 14TB
# - TSBA, Y1Q0A0EUFJDH, 18TB
#
#
# MOBO:
# - DEFAECA8FAEC7DE1
# - 76276163-1498-4304-abb8-066b31f8ccb5
# - 666b16fb-2712-4743-b6b3-49a35e835fe6

drives_uuids_location_size = namedtuple('drives_uuids_location_size', ['uuid', 'location', 'size'])

drives_data = [
    drives_uuids_location_size('666b16fb-2712-4743-b6b3-49a35e835fe6', 'MOBO', '16'),
    drives_uuids_location_size('DEFAECA8FAEC7DE1', 'MOBO', '18'),
    drives_uuids_location_size('76276163-1498-4304-abb8-066b31f8ccb5', 'MOBO', '18'),

    drives_uuids_location_size('Y1Q0A0EUFJDH', '4_8', '18'),
    drives_uuids_location_size('ZLW28R8M', '4_7', '14'),
    drives_uuids_location_size('ZA2DNLBY', '4_6', '10'),
    drives_uuids_location_size('Y1R0A1V0FJDH', '4_5', '18'),
    drives_uuids_location_size('ZL29EZD1', '4_4', '14'),
    drives_uuids_location_size('Y1Q0A0EBFJDH', '4_3', '18'),
    drives_uuids_location_size('3WJ87UJK', '4_2', '18'),
    drives_uuids_location_size('Y1Q0A09JFJDH', '4_1', '18'),

    drives_uuids_location_size('3GG8GH4E', '3_8', '18'),
    drives_uuids_location_size('91T0A1YFFVGG', '3_7', '16'),
    drives_uuids_location_size('ZL2DJJKF', '3_6', '14'),
    drives_uuids_location_size('ZA2DTK2E', '3_5', '10'),
    drives_uuids_location_size('ZL2EBHZY', '3_4', '16'),
    drives_uuids_location_size('ZL2GDWF1', '3_3', '16'),
    drives_uuids_location_size('ZL2E79D9', '3_2', '14'),
    drives_uuids_location_size('Z130A09JFJDH', '3_1', '18'),

    drives_uuids_location_size('3WK2UM2J', '2_8', '18'),
    drives_uuids_location_size('62X0A0FNFJDH', '2_7', '18'),
    drives_uuids_location_size('Z130A0ASFJDH', '2_6', '18'),
    drives_uuids_location_size('ZLW226D6', '2_5', '12'),
    drives_uuids_location_size('62X0A01SFJDH', '2_4', '18'),
    drives_uuids_location_size('62P0A269FJDH', '2_3', '18'),
    drives_uuids_location_size('91T0A20HFVGG', '2_2', '16'),
    drives_uuids_location_size('Y1S0A091FJDH', '2_1', '18'),
]

def get_failing_ids_drive_data():
    found_drive_info = get_drive_info()
    for drive in drives_data:
        if drive.uuid not in found_drive_info:
            LOG.info(f"Drive with uuid '{drive.uuid}' size '{drive.size}' and located in '{drive.location}' not found. "
                     f"please check if plugged in (loose connectors in PSU).")
