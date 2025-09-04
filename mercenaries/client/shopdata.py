from typing import NamedTuple

# MOM unlocks are stored at $51EE7C.
# Each one is a struct with the following format:
# struct {
#   uint32_t id;
#   uint32_t price;  // in dollars
#   uint32_t new;    // 1 if the "new!" flag should appear in the shop
# }
# The price given is the *baseline* price; the effective price displayed in-game
# and charged to you may be more or less depending on your reputation with the
# mafia.
UNLOCK_PTR = 0x0051EE7C

# $51F47C contains additional information:
# struct {
#   uint32_t total_unlocked;  // entries in the unlock array >= this index are ignored
#   uint32_t vehicles_unlocked; // These three are cosmetic only, used for drawing the scrollbar
#   uint32_t supplies_unlocked;
#   uint32_t airstrikes_unlocked;
#   uint32_t last_selected; // index into the unlock array of the currently focused item
# }
METADATA_PTR = 0x0051F47C

class UnlockTemplate(NamedTuple):
  tag: int
  price: int
  type: str
  name: str

# List of unlock struct contents in the format (id, price, type, name).
UNLOCKS = [
  UnlockTemplate(0x00,     35_000,  'vehicle',   'Mafia SUV'),
  UnlockTemplate(0x01,     30_000,  'vehicle',   'H3'),
  UnlockTemplate(0x02,    200_000,  'airstrike', 'Air Superiority'),
  UnlockTemplate(0x03,    250_000,  'airstrike', 'Tank Buster'),
  UnlockTemplate(0x04,    300_000,  'airstrike', 'Cruise Missile Strike'),
  UnlockTemplate(0x05,     45_000,  'airstrike', 'Stealth Fighter Attack'),
  UnlockTemplate(0x06,     50_000,  'airstrike', 'Surgical Strike'),
  UnlockTemplate(0x07,     75_000,  'airstrike', 'Gunship Support'),
  UnlockTemplate(0x08,    150_000,  'airstrike', 'Gunship Support II'),
  UnlockTemplate(0x09,    225_000,  'airstrike', 'Gunship Support III'),
  UnlockTemplate(0x0A,     75_000,  'airstrike', 'Strategic Missile Strike'),
  UnlockTemplate(0x0B,    350_000,  'airstrike', 'Bunker Buster Bomb'),
  UnlockTemplate(0x0C,     50_000,  'airstrike', 'Artillery Strike'),
  UnlockTemplate(0x0D,    100_000,  'airstrike', 'Artillery Barrage'),
  UnlockTemplate(0x0E,    200_000,  'airstrike', 'Artillery Bombardment'),
  UnlockTemplate(0x0F,     65_000,  'airstrike', 'Cluster Bomb'),
  UnlockTemplate(0x10,    500_000,  'airstrike', 'Carpet Bomb'),
  UnlockTemplate(0x11,      8_000,  'supplies',  'Covert Supply Drop'),
  UnlockTemplate(0x12,      6_500,  'supplies',  'Allies Supply Drop'),
  UnlockTemplate(0x13,     12_000,  'supplies',  'Special Weapons Drop'),
  UnlockTemplate(0x14,      6_000,  'supplies',  'Chinese Supply Drop'),
  UnlockTemplate(0x15,      2_500,  'supplies',  'Medical Supply Drop'),
  UnlockTemplate(0x16,      7_500,  'supplies',  'North Korean Supply Drop'),
  UnlockTemplate(0x17,      4_000,  'supplies',  'Russian Supply Drop'),
  UnlockTemplate(0x18,     15_000,  'supplies',  'Heavy Weapons Drop'),
  UnlockTemplate(0x19,     40_000,  'vehicle',   'N. Korean BRDM Scout'),
  UnlockTemplate(0x1A,     75_000,  'vehicle',   'N. Korean BMP APC'),
  UnlockTemplate(0x1B,     25_000,  'vehicle',   'N. Korean BTR APC'),
  UnlockTemplate(0x1C,     12_000,  'vehicle',   'N. Korean Sungri Scout'),
  UnlockTemplate(0x1D,      5_000,  'vehicle',   'Civilian Car'),
  UnlockTemplate(0x1E,     65_000,  'vehicle',   'Allies UH-60'),
  UnlockTemplate(0x1F,     95_000,  'vehicle',   'Mafia MD-530'),
  UnlockTemplate(0x20,     35_000,  'vehicle',   'S. Korean K966 Scout'),
  UnlockTemplate(0x21,     25_000,  'vehicle',   'S. Korean K1025 Scout'),
  UnlockTemplate(0x22,     60_000,  'vehicle',   'S. Korean K200 APC'),
  UnlockTemplate(0x23,     40_000,  'vehicle',   'Allied M1126 APC'),
  UnlockTemplate(0x24,     10_000,  'vehicle',   'Baggage Car'),
  UnlockTemplate(0x25,     15_000,  'vehicle',   'Chinese BJ2020 Scout'),
  UnlockTemplate(0x26,     50_000,  'vehicle',   'Chinese Type 89 APC'),
  UnlockTemplate(0x27,     25_000,  'vehicle',   'Allied M1025 Scout'),
  UnlockTemplate(0x28,     30_000,  'vehicle',   'Mafia Technical (AT)'),
  UnlockTemplate(0x29,     20_000,  'vehicle',   'Mafia Technical (MG)'),
  UnlockTemplate(0x2A,     35_000,  'vehicle',   'Mafia Technical (GL)'),
  UnlockTemplate(0x2B,     12_000,  'supplies',  'Sniper Supply Drop'),
  UnlockTemplate(0x2C,      8_000,  'supplies',  'Vehicle Ammo Drop'),
  UnlockTemplate(0x2D,     13_000,  'supplies',  'Vehicle Repair Drop'),
  UnlockTemplate(0x2E,     65_000,  'vehicle',   'N. Korean ZSU-57 Anti-Air'),
  UnlockTemplate(0x2F,     20_000,  'vehicle',   'Press Truck'),
  UnlockTemplate(0x30,     35_000,  'vehicle',   'Allied M1027 Anti-Air'),
  UnlockTemplate(0x31,     10_000,  'vehicle',   'N. Korean Transport'),
  UnlockTemplate(0x32,     25_000,  'vehicle',   'Civilian Street Racer'),
  UnlockTemplate(0x33,    100_000,  'vehicle',   'Chinese Type 95 Anti-Air'),
  UnlockTemplate(0x34,    450_000,  'airstrike', 'Fuel-Air Bomb'),
  UnlockTemplate(0x35,    115_000,  'vehicle',   'N. Korean MD-500'),
  UnlockTemplate(0x36,     35_000,  'vehicle',   'Mafia VIP Car'),
  UnlockTemplate(0x37,     20_000,  'vehicle',   'Chinese Fuel Truck'),
  UnlockTemplate(0x38,     30_000,  'supplies',  'Vehicle Support Drop'),
  UnlockTemplate(0x39,     15_000,  'supplies',  'Sniper Rifle Drop'),
  UnlockTemplate(0x3A,     18_000,  'supplies',  'Anti-Air Rocket Drop'),
  UnlockTemplate(0x3B,     18_000,  'supplies',  'Anti-Tank Rocket Drop'),
  UnlockTemplate(0x3C,     20_000,  'supplies',  'Advanced Weapons Drop'),
  UnlockTemplate(0x3D,  1_000_000,  'supplies',  'Cheat Weapons Drop'),
  UnlockTemplate(0x3E,      8_000,  'supplies',  'Demolitions Supply Drop'),
]

NROF_UNLOCKS = len(UNLOCKS)
