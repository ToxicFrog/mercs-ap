from typing import NamedTuple

from BaseClasses import ItemClassification

from ..id import next_id

class ShopItem(NamedTuple):
  id: int
  tag: int   # Internal tag used by the engine to represent this
  price: int # Base price before reputation modifiers
  type: str  # vehicle, airstrike, or supplies; might in the future want to distinguish subtypes
  title: str  # User-facing name

  def name(self):
    return f'{self.type.capitalize()}: {self.title}'

  def count(self, options):
    return int(options.shop_unlock_count)

  def groups(self):
    return {'progression', 'shop', self.type}

  def classification(self):
    return ItemClassification.progression


SHOP_ITEMS = [
  ShopItem(next_id(), 0x00,     35_000,  'vehicle',   'Mafia SUV'),
  ShopItem(next_id(), 0x01,     30_000,  'vehicle',   'H3'),
  ShopItem(next_id(), 0x02,    200_000,  'airstrike', 'Air Superiority'),
  ShopItem(next_id(), 0x03,    250_000,  'airstrike', 'Tank Buster'),
  ShopItem(next_id(), 0x04,    300_000,  'airstrike', 'Cruise Missile Strike'),
  ShopItem(next_id(), 0x05,     45_000,  'airstrike', 'Stealth Fighter Attack'),
  ShopItem(next_id(), 0x06,     50_000,  'airstrike', 'Surgical Strike'),
  ShopItem(next_id(), 0x07,     75_000,  'airstrike', 'Gunship Support'),
  ShopItem(next_id(), 0x08,    150_000,  'airstrike', 'Gunship Support II'),
  ShopItem(next_id(), 0x09,    225_000,  'airstrike', 'Gunship Support III'),
  ShopItem(next_id(), 0x0A,     75_000,  'airstrike', 'Strategic Missile Strike'),
  ShopItem(next_id(), 0x0B,    350_000,  'airstrike', 'Bunker Buster Bomb'),
  ShopItem(next_id(), 0x0C,     50_000,  'airstrike', 'Artillery Strike'),
  ShopItem(next_id(), 0x0D,    100_000,  'airstrike', 'Artillery Barrage'),
  ShopItem(next_id(), 0x0E,    200_000,  'airstrike', 'Artillery Bombardment'),
  ShopItem(next_id(), 0x0F,     65_000,  'airstrike', 'Cluster Bomb'),
  ShopItem(next_id(), 0x10,    500_000,  'airstrike', 'Carpet Bomb'),
  ShopItem(next_id(), 0x11,      8_000,  'supplies',  'Covert Supply Drop'),
  ShopItem(next_id(), 0x12,      6_500,  'supplies',  'Allies Supply Drop'),
  ShopItem(next_id(), 0x13,     12_000,  'supplies',  'Special Weapons Drop'),
  ShopItem(next_id(), 0x14,      6_000,  'supplies',  'Chinese Supply Drop'),
  ShopItem(next_id(), 0x15,      2_500,  'supplies',  'Medical Supply Drop'),
  ShopItem(next_id(), 0x16,      7_500,  'supplies',  'North Korean Supply Drop'),
  ShopItem(next_id(), 0x17,      4_000,  'supplies',  'Russian Supply Drop'),
  ShopItem(next_id(), 0x18,     15_000,  'supplies',  'Heavy Weapons Drop'),
  ShopItem(next_id(), 0x19,     40_000,  'vehicle',   'N. Korean BRDM Scout'),
  ShopItem(next_id(), 0x1A,     75_000,  'vehicle',   'N. Korean BMP APC'),
  ShopItem(next_id(), 0x1B,     25_000,  'vehicle',   'N. Korean BTR APC'),
  ShopItem(next_id(), 0x1C,     12_000,  'vehicle',   'N. Korean Sungri Scout'),
  ShopItem(next_id(), 0x1D,      5_000,  'vehicle',   'Civilian Car'),
  ShopItem(next_id(), 0x1E,     65_000,  'vehicle',   'Allies UH-60'),
  ShopItem(next_id(), 0x1F,     95_000,  'vehicle',   'Mafia MD-530'),
  ShopItem(next_id(), 0x20,     35_000,  'vehicle',   'S. Korean K966 Scout'),
  ShopItem(next_id(), 0x21,     25_000,  'vehicle',   'S. Korean K1025 Scout'),
  ShopItem(next_id(), 0x22,     60_000,  'vehicle',   'S. Korean K200 APC'),
  ShopItem(next_id(), 0x23,     40_000,  'vehicle',   'Allied M1126 APC'),
  ShopItem(next_id(), 0x24,     10_000,  'vehicle',   'Baggage Car'),
  ShopItem(next_id(), 0x25,     15_000,  'vehicle',   'Chinese BJ2020 Scout'),
  ShopItem(next_id(), 0x26,     50_000,  'vehicle',   'Chinese Type 89 APC'),
  ShopItem(next_id(), 0x27,     25_000,  'vehicle',   'Allied M1025 Scout'),
  ShopItem(next_id(), 0x28,     30_000,  'vehicle',   'Mafia Technical (AT)'),
  ShopItem(next_id(), 0x29,     20_000,  'vehicle',   'Mafia Technical (MG)'),
  ShopItem(next_id(), 0x2A,     35_000,  'vehicle',   'Mafia Technical (GL)'),
  ShopItem(next_id(), 0x2B,     12_000,  'supplies',  'Sniper Supply Drop'),
  ShopItem(next_id(), 0x2C,      8_000,  'supplies',  'Vehicle Ammo Drop'),
  ShopItem(next_id(), 0x2D,     13_000,  'supplies',  'Vehicle Repair Drop'),
  ShopItem(next_id(), 0x2E,     65_000,  'vehicle',   'N. Korean ZSU-57 Anti-Air'),
  ShopItem(next_id(), 0x2F,     20_000,  'vehicle',   'Press Truck'),
  ShopItem(next_id(), 0x30,     35_000,  'vehicle',   'Allied M1027 Anti-Air'),
  ShopItem(next_id(), 0x31,     10_000,  'vehicle',   'N. Korean Transport'),
  ShopItem(next_id(), 0x32,     25_000,  'vehicle',   'Civilian Street Racer'),
  ShopItem(next_id(), 0x33,    100_000,  'vehicle',   'Chinese Type 95 Anti-Air'),
  ShopItem(next_id(), 0x34,    450_000,  'airstrike', 'Fuel-Air Bomb'),
  ShopItem(next_id(), 0x35,    115_000,  'vehicle',   'N. Korean MD-500'),
  ShopItem(next_id(), 0x36,     35_000,  'vehicle',   'Mafia VIP Car'),
  ShopItem(next_id(), 0x37,     20_000,  'vehicle',   'Chinese Fuel Truck'),
  ShopItem(next_id(), 0x38,     30_000,  'supplies',  'Vehicle Support Drop'),
  ShopItem(next_id(), 0x39,     15_000,  'supplies',  'Sniper Rifle Drop'),
  ShopItem(next_id(), 0x3A,     18_000,  'supplies',  'Anti-Air Rocket Drop'),
  ShopItem(next_id(), 0x3B,     18_000,  'supplies',  'Anti-Tank Rocket Drop'),
  ShopItem(next_id(), 0x3C,     20_000,  'supplies',  'Advanced Weapons Drop'),
  ShopItem(next_id(), 0x3D,  1_000_000,  'supplies',  'Cheat Weapons Drop'),
  ShopItem(next_id(), 0x3E,      8_000,  'supplies',  'Demolitions Supply Drop'),
]
