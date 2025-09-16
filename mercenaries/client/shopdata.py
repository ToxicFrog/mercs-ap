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
  template: str  # without 'template_support_' prefix
  name: str

# List of unlock struct contents in the format (id, price, type, name).
UNLOCKS = [
  UnlockTemplate(0x00,     35_000,  'vehicle',   'deliverH2', 'Mafia SUV'),
  UnlockTemplate(0x01,     30_000,  'vehicle',   'deliverH3', 'H3'),
  UnlockTemplate(0x02,    200_000,  'airstrike', 'p_airsuperiority', 'Air Superiority'),
  UnlockTemplate(0x03,    250_000,  'airstrike', 'p_tankbuster', 'Tank Buster'),
  UnlockTemplate(0x04,    300_000,  'airstrike', 'p_cruisemissile', 'Cruise Missile Strike'),
  UnlockTemplate(0x05,     45_000,  'airstrike', 'p_smartbomb', 'Stealth Fighter Attack'),
  UnlockTemplate(0x06,     50_000,  'airstrike', 'p_surgicalstrike', 'Surgical Strike'),
  UnlockTemplate(0x07,     75_000,  'airstrike', 'p_gunship', 'Gunship Support'),
  UnlockTemplate(0x08,    150_000,  'airstrike', 'p_gunship2', 'Gunship Support II'),
  UnlockTemplate(0x09,    225_000,  'airstrike', 'p_gunship3', 'Gunship Support III'),
  UnlockTemplate(0x0A,     75_000,  'airstrike', 'strategicmissile', 'Strategic Missile Strike'),
  UnlockTemplate(0x0B,    350_000,  'airstrike', 'p_bunkerbuster', 'Bunker Buster Bomb'),
  UnlockTemplate(0x0C,     50_000,  'airstrike', 'p_artillery', 'Artillery Strike'),
  UnlockTemplate(0x0D,    100_000,  'airstrike', 'p_artillery2', 'Artillery Barrage'),
  UnlockTemplate(0x0E,    200_000,  'airstrike', 'p_artillery3', 'Artillery Bombardment'),
  UnlockTemplate(0x0F,     65_000,  'airstrike', 'p_clusterbomb', 'Cluster Bomb'),
  UnlockTemplate(0x10,    500_000,  'airstrike', 'p_carpetbomb', 'Carpet Bomb'),
  UnlockTemplate(0x11,      8_000,  'supplies',  'crate_mafiaCovert', 'Covert Supply Drop'),
  UnlockTemplate(0x12,      6_500,  'supplies',  'crate_mafiaAllies', 'Allies Supply Drop'),
  UnlockTemplate(0x13,     12_000,  'supplies',  'crate_mafiaSpecial', 'Special Weapons Drop'),
  UnlockTemplate(0x14,      6_000,  'supplies',  'crate_mafiaChina', 'Chinese Supply Drop'),
  UnlockTemplate(0x15,      2_500,  'supplies',  'crate_mafiaHealth', 'Medical Supply Drop'),
  UnlockTemplate(0x16,      7_500,  'supplies',  'crate_nk', 'North Korean Supply Drop'),
  UnlockTemplate(0x17,      4_000,  'supplies',  'crate_mafia', 'Russian Supply Drop'),
  UnlockTemplate(0x18,     15_000,  'supplies',  'crate_mafiaHeavy', 'Heavy Weapons Drop'),
  UnlockTemplate(0x19,     40_000,  'vehicle',   'deliverStolenNKBRDM', 'N. Korean BRDM Scout'),
  UnlockTemplate(0x1A,     75_000,  'vehicle',   'deliverStolenNKBMP', 'N. Korean BMP APC'),
  UnlockTemplate(0x1B,     25_000,  'vehicle',   'deliverStolenNKBTR60', 'N. Korean BTR APC'),
  UnlockTemplate(0x1C,     12_000,  'vehicle',   'deliverStolenNKJeep', 'N. Korean Sungri Scout'),
  UnlockTemplate(0x1D,      5_000,  'vehicle',   'deliverStolenCivCar', 'Civilian Car'),
  UnlockTemplate(0x1E,     65_000,  'vehicle',   'deliverStolenAlliesBlackhawk', 'Allies UH-60'),
  UnlockTemplate(0x1F,     95_000,  'vehicle',   'deliverLittleBird', 'Mafia MD-530'),
  UnlockTemplate(0x20,     35_000,  'vehicle',   'deliverStolenSKHumveeAT', 'S. Korean K966 Scout'),
  UnlockTemplate(0x21,     25_000,  'vehicle',   'deliverStolenSKHumveeMG', 'S. Korean K1025 Scout'),
  UnlockTemplate(0x22,     60_000,  'vehicle',   'deliverStolenSKAPC', 'S. Korean K200 APC'),
  UnlockTemplate(0x23,     40_000,  'vehicle',   'deliverStolenAlliesStryker', 'Allied M1126 APC'),
  UnlockTemplate(0x24,     10_000,  'vehicle',   'deliverStolenBaggageCar', 'Baggage Car'),
  UnlockTemplate(0x25,     15_000,  'vehicle',   'deliverStolenChinaJeep', 'Chinese BJ2020 Scout'),
  UnlockTemplate(0x26,     50_000,  'vehicle',   'deliverStolenChinaAPC', 'Chinese Type 89 APC'),
  UnlockTemplate(0x27,     25_000,  'vehicle',   'deliverStolenAlliesHumvee', 'Allied M1025 Scout'),
  UnlockTemplate(0x28,     30_000,  'vehicle',   'deliverTechnicalAT', 'Mafia Technical (AT)'),
  UnlockTemplate(0x29,     20_000,  'vehicle',   'deliverTechnicalMG', 'Mafia Technical (MG)'),
  UnlockTemplate(0x2A,     35_000,  'vehicle',   'deliverTechnicalGL', 'Mafia Technical (GL)'),
  UnlockTemplate(0x2B,     12_000,  'supplies',  'crate_mafiaSniper', 'Sniper Supply Drop'),
  UnlockTemplate(0x2C,      8_000,  'supplies',  'crate_MafiaAmmoveh', 'Vehicle Ammo Drop'),
  UnlockTemplate(0x2D,     13_000,  'supplies',  'crate_MafiaArmor', 'Vehicle Repair Drop'),
  UnlockTemplate(0x2E,     65_000,  'vehicle',   'deliverStolenZSU', 'N. Korean ZSU-57 Anti-Air'),
  UnlockTemplate(0x2F,     20_000,  'vehicle',   'deliverStolenPressTruck', 'Press Truck'),
  UnlockTemplate(0x30,     35_000,  'vehicle',   'deliverStolenAlliesAvenger', 'Allied M1027 Anti-Air'),
  UnlockTemplate(0x31,     10_000,  'vehicle',   'deliverStolenNKTransport', 'N. Korean Transport'),
  UnlockTemplate(0x32,     25_000,  'vehicle',   'deliverStolenSportsCar', 'Civilian Street Racer'),
  UnlockTemplate(0x33,    100_000,  'vehicle',   'deliverStolenTunguska', 'Chinese Type 95 Anti-Air'),
  UnlockTemplate(0x34,    450_000,  'airstrike', 'p_fuelairbomb', 'Fuel-Air Bomb'),
  UnlockTemplate(0x35,    115_000,  'vehicle',   'deliverStolenNKLittleBird', 'N. Korean MD-500'),
  UnlockTemplate(0x36,     35_000,  'vehicle',   'deliverVIPCar', 'Mafia VIP Car'),
  UnlockTemplate(0x37,     20_000,  'vehicle',   'deliverStolenChinaFuelTruck', 'Chinese Fuel Truck'),
  UnlockTemplate(0x38,     30_000,  'supplies',  'crate_mafiaVehicle', 'Vehicle Support Drop'),
  UnlockTemplate(0x39,     15_000,  'supplies',  'crate_sniperrifle', 'Sniper Rifle Drop'),
  UnlockTemplate(0x3A,     18_000,  'supplies',  'crate_stinger', 'Anti-Air Rocket Drop'),
  UnlockTemplate(0x3B,     18_000,  'supplies',  'crate_atrocket', 'Anti-Tank Rocket Drop'),
  UnlockTemplate(0x3C,     20_000,  'supplies',  'crate_mafiaAdvanced', 'Advanced Weapons Drop'),
  UnlockTemplate(0x3D,  1_000_000,  'supplies',  'crate_mafiaCheatgun', 'Cheat Weapons Drop'),
  UnlockTemplate(0x3E,      8_000,  'supplies',  'crate_mafiaC4', 'Demolitions Supply Drop'),
]

NROF_UNLOCKS = len(UNLOCKS)

# The following templates appear in ASSETS.DSK but not in SHOP.INI. I believe
# they are the non-Mafia versions of the above used in some missions, plus possibly
# some that you can't get in the shop at all.
EXTRA_TEMPLATES = [
  # Entirely new airstrikes:
  'hvySmartBomb',

  # Versions of the airstrikes without the p_ prefix:
  'airsuperiority',
  'artillery',
  'artillery2',
  'artillery3',
  'bunkerbuster',
  'carpetbomb',
  'clusterbomb',
  'cruisemissile',
  'fuelairbomb',
  'guidedmissile',
  'gunship',
  'gunship2',
  'gunship3',
  'smartbomb',
  'strategicmissile',
  'surgicalstrike',
  'tankbuster',

  # Versions of the crates not present in the shop; these are probably the same
  # contents with a different delivery vehicle:
  'crate_Allies'
  'crate_AlliesAmmoVeh'
  'crate_AlliesC4'
  'crate_AlliesHeavy'
  'crate_AlliesStinger'
  'crate_China'
  'crate_ChinaAmmoVeh'
  'crate_ChinaArmor'
  'crate_ChinaHeavy'
  'crate_chinaStinger'
  'crate_ChinaVehicle'
  'crate_SK'
  'crate_SKC4'
  'crate_SKCovert'
  'crate_SKHeavy'
  'crate_SKSniper'
  'crate_skStinger'

  # Versions of vehicle deliveries that are not available in the shop:
  'deliverAlliesHumvee',
  'deliverAlliesStryker',
  'deliverChinaJeep',
  'deliverSKAPC',
  'deliverSKHumveeAT',
  'deliverSKHumveeMG',
  'deliverstolenalliesAvenger1',
  'deliverStolenCivCargoTruck',
  'deliverStolenNKCargoTruck',
  'deliverStolenPressTruck1',
  'deliverVIPCar',
]
