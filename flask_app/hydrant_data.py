"""
Seed data for the hydrant section, transcribed from paper records:

  * White sheets — "Spring Valley Volunteer Fire Dept Fire Hydrant Location" (2017),
    hydrants 1-27, with main line size, outlets and owner.
  * White handwritten sheet dated 12/16/2017 — pressure (PSI) checks keyed to the
    2017 hydrant numbers.
  * Yellow sheets (2026 flow tests) — GPM @ PSI through the listed nozzle size.
      - Ronnie Smith / Christian Green sheet, 09:30-15:53  -> 2026-09-15
      - Andrea sheet (Josh, Manager / Water Dept.)          -> 2026-09-24
    Each yellow entry was matched to the 2017 list by GPS (all within ~35 m, one
    at 100 m).  Entries with no 2017 match became hydrants 28-33.

GPS is decimal degrees.  Where a 2026 reading exists it is used; otherwise the
2017 degrees/decimal-minutes value was converted.
"""

RONNIE = 'Ronnie Smith, Christian Green'
ANDREA = 'Andrea'
Y2017 = 'SVVFD 2017 survey'

# number, name, latitude, longitude, main_size, outlets, owner, notes
HYDRANTS = [
    (1,  'Kilabrew Rd, 400 yds E of Lost City Rd', 35.9879147, -95.1333963, '6"', '2-2.5" & 1-4.5"', 'Tax Board', '1/4 mile E of 4-way at Lost City Rd'),
    (2,  'Lost City Community Center', 35.984057, -95.136302, '3"', '1-2.5"', 'Lost City School', ''),
    (3,  'W 720 Rd - Hyd #1 (9570 W 720 Rd)', 35.9732954, -95.1258020, '8"', '4.5" with 2-2.5"', 'Cherokee Nation', 'First of four on W 720 Rd, west to east'),
    (4,  'W 720 Rd - Hyd #2, top of the hill (near 10443)', 35.9733611, -95.1116862, '6"', '4.5" with 2-2.5"', 'Cherokee Nation', ''),
    (5,  'W 720 Rd - Hyd #3, E of 440 Rd (near 11350)', 35.9733331, -95.0949194, '6"', '4.5" with 2-2.5"', 'Cherokee Nation', ''),
    (6,  'W 720 Rd - Hyd #4 (11426 W 720 Rd)', 35.9733155, -95.0922318, '6"', '4.5" with 2-2.5"', 'Cherokee Nation', ''),
    (7,  'Shady Grove School (Shady Grove School & 440 Rd)', 35.9587852, -95.1007777, '8"', '5.25" with 1-4.5" and 2-2.5"', 'RWD#11', ''),
    (8,  'N 440 Rd at Water Tower', 35.976980, -95.171998, '8"', '4.5" with 1-4.5" and 2-2.5"', 'Tax Board',
         'GPS from 2017 sheet; longitude is identical to hydrant 9 and may be a typo - verify in the field'),
    (9,  'N 400 Rd & W 700 Rd (12156 N 400 Rd)', 36.0020721, -95.1718170, '6"', '4.5" with 1-4.5" and 2-2.5"', 'Tax Board', ''),
    (10, 'W 700 Rd / N 390 Rd (12024 W 700 Rd)', 36.0017130, -95.1899494, '6"', '5.25" with 2-2.5"', 'Tax Board', ''),
    (11, 'Groat Rd & Clear Creek Rd', 35.9731806, -95.2071373, '6"', '4.5" with 2-2.5"', 'Tax Board', 'W Groat Rd, E of N Clear Creek Rd'),
    (12, 'N Clear Creek Rd, N of the store', 35.9595575, -95.2077073, '2"', '2" with 1-2.5"', 'Tax Board', 'Side of the hill'),
    (13, 'Station 2', 35.9298689, -95.2380230, '2.5"', '2" with 1-2.5"', 'Tax Board', ''),
    (14, 'Hickory Hills Dr & N 357 Rd (16484 Hickory Hills)', 35.9370268, -95.2570003, '6"', '5.25" with 2-2.5"', 'Tax Board',
         'Needs valve wrench (2017). Valve leaks a little - if dug up may need new valve (2026).'),
    (15, 'State Park - Group Camp', 35.9257000, -95.2547200, '6"', '5.25" with 4.5" and 2-2.5"', 'State', 'Sequoyah State Park'),
    (16, 'State Park - Golf Course (Pro Shop)', 35.8988622, -95.2438145, '6"', '5.25" with 4.5" and 2-2.5"', 'State', 'Sequoyah State Park'),
    (17, 'State Park - East of Nature Center', 35.8967470, -95.2408309, '6"', '4.5" with 1-4.5" and 2-2.5"', 'State', 'Sequoyah State Park'),
    (18, 'State Park - Cabins (Cabin 323)', 35.891465, -95.241552, '6"', '5.25" with 1-4.5" and 2-2.5"', 'State', 'Sequoyah State Park'),
    (19, 'State Park - North side of Lodge by parking lot', 35.8896289, -95.2414086, '6"', '5.25" with 1-4.5" and 2-2.5"', 'State', 'Sequoyah State Park; near lodge pool'),
    (20, 'State Park - Water Plant', 35.893170, -95.241090, '6"', '5.25" with 1-4.5" and 2-2.5"', 'State', 'Sequoyah State Park'),
    (21, 'N Sunset Valley Rd - Nursery Entrance #4', 35.9451224, -95.2434816, '6"', '5.25" with 1-4.5" and 2-2.5"', 'Tax Board', 'West side of road, near 15933 Sunset Valley Rd'),
    (22, 'Sunset Valley - Northern Dr & N Eastern Dr', 35.9846104, -95.2392367, '4"', '5.25" with 1-4.5" and 2-2.5"', 'RWD#9', ''),
    (23, 'Sunset Valley - Riviera Dr & N Eastern Dr', 35.9804871, -95.2433457, '4"', '5.25" with 1-4.5" and 2-2.5"', 'RWD#9', ''),
    (24, 'Sunset Valley - Sunset Dr, S of 13806', 35.975668, -95.246948, '4"', '5.25" with 1-4.5" and 2-2.5"', 'RWD#9', ''),
    (25, 'Sunset Valley - N Riviera Dr & W Southern Ave', 35.9732522, -95.2502589, '2"', '5.25" with 1-4.5" and 2-2.5"', 'RWD#9', ''),
    (26, 'Sunset Valley - W 712 Rd & N Shoreline Dr', 35.9852916, -95.2468786, '4"', '5.25" with 1-4.5" and 2-2.5"', 'RWD#9', 'Shoreline & Elm'),
    (27, 'Sunset Valley - Big Water Tower (Quail Dr / Redbud)', 35.9867856, -95.2377417, '2"', '5.25" with 1-4.5" and 2-2.5"', 'RWD#9', ''),
    # Not on the 2017 list
    (28, 'Lost City Rd & Grace Hudlen Rd', 35.9731619, -95.1334604, '', '', '', 'Added from 2026 test sheet'),
    (29, 'Grace Hudlen Rd, N of W 730 Rd', 35.9573674, -95.1716574, '', '', '', 'Added from 2026 test sheet'),
    (30, 'Meadowlark Ln & Hwy 51', 35.9371053, -95.1988587, '', '', '', 'Added from 2026 test sheets (GPS on one sheet, flow on the other)'),
    (31, 'Bear Rock Store / Hwy 51', 35.9298317, -95.2490542, '', '', '', 'Added from 2026 test sheet'),
    (32, 'W 730 Rd, E of N Clear Creek Rd', 35.9588460, -95.1931623, '', '', '', 'Added from 2026 test sheet'),
    (33, 'W 710 Rd', None, None, '', '', '', 'Listed on 2026 sheet but no GPS or test recorded'),
]

# hydrant number, test_date, gpm, psi, nozzle_size, tested_by, notes
TESTS = [
    # 12/16/2017 pressure checks
    (14, '2017-12-16', None, 4,    '', Y2017, 'Needs valve wrench'),
    (3,  '2017-12-16', None, 23,   '', Y2017, ''),
    (4,  '2017-12-16', None, 15,   '', Y2017, ''),
    (5,  '2017-12-16', None, 12,   '', Y2017, ''),
    (21, '2017-12-16', None, 18.5, '', Y2017, ''),
    (15, '2017-12-16', None, 3,    '', Y2017, ''),
    (16, '2017-12-16', None, 11,   '', Y2017, ''),
    (17, '2017-12-16', None, 14.5, '', Y2017, ''),
    (19, '2017-12-16', None, 14,   '', Y2017, 'Lodge pool'),
    (18, '2017-12-16', None, 14,   '', Y2017, ''),
    (20, '2017-12-16', None, 8,    '', Y2017, ''),
    (13, '2017-12-16', None, 4,    '', Y2017, ''),
    (23, '2017-12-16', None, 1,    '', Y2017, ''),
    (22, '2017-12-16', None, 2,    '', Y2017, ''),
    (27, '2017-12-16', None, 1,    '', Y2017, ''),
    (26, '2017-12-16', None, 1,    '', Y2017, ''),
    (25, '2017-12-16', None, 8,    '', Y2017, 'Handwriting unclear - may be 3 PSI'),
    (24, '2017-12-16', None, 5,    '', Y2017, ''),
    (12, '2017-12-16', None, 5,    '', Y2017, ''),
    (2,  '2017-12-16', None, 1,    '', Y2017, ''),
    (6,  '2017-12-16', None, 9,    '', Y2017, ''),

    # 2026 flow tests - Ronnie Smith / Christian Green
    (1,  '2026-09-15', 493, 16, '2"',    RONNIE, ''),
    (28, '2026-09-15', 956, 40, '2.25"', RONNIE, ''),
    (3,  '2026-09-15', 855, 32, '2.25"', RONNIE, ''),
    (4,  '2026-09-15', 616, 16, '2.25"', RONNIE, ''),
    (5,  '2026-09-15', 536, 12, '2.25"', RONNIE, ''),
    (6,  '2026-09-15', 536, 12, '2.25"', RONNIE, ''),
    (7,  '2026-09-15', 956, 40, '2.25"', RONNIE, ''),
    (29, '2026-09-15', 536, 12, '2.25"', RONNIE, ''),
    (14, '2026-09-15', 396, 10, '2"',    RONNIE, 'Valve leaks a little; may need new valve if dug up'),
    (31, '2026-09-15', 220, 10, '1.5"',  RONNIE, ''),
    (15, '2026-09-15', 260, 14, '1.5"',  RONNIE, ''),
    (16, '2026-09-15', 324, 22, '1.5"',  RONNIE, ''),
    (19, '2026-09-15', 652, 18, '2.25"', RONNIE, ''),
    (17, '2026-09-15', 616, 16, '2.25"', RONNIE, ''),
    (13, '2026-09-15', 296, 10, '1.75"', RONNIE, ''),

    # 2026 flow tests - Andrea
    (10, '2026-09-24', 220, 10, '1.5"',  ANDREA, ''),
    (9,  '2026-09-24', 310, 20, '1.5"',  ANDREA, ''),
    (11, '2026-09-24', 493, 16, '2"',    ANDREA, ''),
    (27, '2026-09-24', 110, 5,  '1.5"',  ANDREA, ''),
    (22, '2026-09-24', 200, 8,  '1.5"',  ANDREA, ''),
    (23, '2026-09-24', 220, 10, '1.5"',  ANDREA, ''),
    (26, '2026-09-24', 373, 30, '1.5"',  ANDREA, ''),
    (25, '2026-09-24', 228, 16, '1.5"',  ANDREA, ''),
    (21, '2026-09-24', 678, 20, '2.25"', ANDREA, ''),
    (30, '2026-09-24', 310, 20, '1.5"',  ANDREA, ''),
    (12, '2026-09-24', 828, 30, '2.25"', ANDREA, ''),
    (32, '2026-09-24', 536, 12, '2.25"', ANDREA, ''),
]
