'''
Code patches for the Mercenaries rando.
'''

from .lopcode import LuaOpcode
from .lua import LUA_TNUMBER, LUA_TSTRING, LUA_TBOOL

def patch(globals):
  patch_intel(globals)
  # TODO: Not needed since tCurrentMissions is available in most contexts?
  patch_sgsa(globals)
  patch_afmc(globals)
  redirect_debug_prints(globals)

  afmc = globals['AttemptFactionMoodClamp'].val()
  return (
    globals['gameflow_GetIntelTotal'].val().getk(0), # Intel counter
    afmc.getk(9), # Money bonus
    afmc.getk(11), # Message buffer
    afmc.getk(13), # Message flag
    { # Reputation floors
      'allies': afmc.getk(5),
      'china': afmc.getk(6),
      'mafia': afmc.getk(7),
      'sk':  afmc.getk(8),
    }
  )

def redirect_debug_prints(globals):
  globals['Debug_Printf'].set(globals['AttemptFactionMoodClamp'])
  globals['util_PrintDebugMsg'].set(globals['AttemptFactionMoodClamp'])

def patch_intel(globals):
  '''
  Patch gameflow_GetIntelTotal to return a constant value that we control.

  The first instruction already loads k0 into r0, so all we need to do is patch
  the second instruction to return it.
  '''
  with globals['gameflow_GetIntelTotal'].val().lock() as f:
    f.setk(0, 0.0)
    f.patch(1, [
      LuaOpcode('RETURN', A=1, B=2),
    ])

def patch_sgsa(globals):
  '''
  Patch gameflow_ShouldGameStateApply to extract mission completion information.

  It already has that information conveniently packed into a table on the stack,
  so we just repurpose three instructions previously used for debug output to
  (a) store that information in a global and (b) exit early without doing anything
  else if called without arguments (i.e. by us).
  '''
  with globals['gameflow_ShouldGameStateApply'].val().lock() as f:
    f.patch(24, [
      LuaOpcode('SETGLOBAL', A=5, Bx=1), # set _G.mission_accepted to r5, which is the info table
      LuaOpcode('TEST', A=0, B=0, C=0), # test if r0 is nil, and if so
      LuaOpcode('JMP', sBx=50), # jump to the end of the function
    ])

def patch_afmc(globals):
  '''
  Patch AttemptFactionMoodClamp to adjust mood floors as we see fit, and call
  our other patched functions.

  This is where most of the work happens:
  - call our other patched functions to check intel and mission progress
  - apply faction mood floor adjustments
  - give the player money
  - display HUD messages

  Our main constraint is the constant table. Here's the table for AFMC. Entries that
  we edit are marked with a +. Entries that we do not edit, but are still using,
  are marked with a -.

  At present we have 9 constants left over. If we exceed that we'll need to chain
  to something else.

  +   CONST$00C4D840 k0  'gameflow_ShouldGameStateApply' ; called
  +   CONST$00C4D848 k1  'gameflow_AttemptAceMissionUnlock' ; called
  +   CONST$00C4D850 k2  'bDebugOutput'  ; used as the idempotency flag global
  +   CONST$00C4D858 k3  'Player_SetMoney'  ; called
  +   CONST$00C4D860 k4  'Player_GetMoney'  ; called
  +   CONST$00C4D868 k5  -100.0 allies mood floor
  +   CONST$00C4D870 k6  -100.0 china mood floor
  +   CONST$00C4D878 k7  -100.0 mafia mood floor
  +   CONST$00C4D880 k8  -100.0 sk mood floor
  +   CONST$00C4D888 k9  0.0 money bonus
  +   CONST$00C4D890 k10 'Ui_PrintHudMessage' ; called, k11 is used as scratch space for the message
  +   CONST$00C4D898 k11 '[global.lua] AttemptFactionMoodClamp: just finished first mission sequence; unclamping faction mood\n' [h=44BB274C,$00AA23C0]
      CONST$00C4D8A0 k12 'Utility_WriteNumberToScribbleMemory' [h=DCF55147,$009DC740]
  +   CONST$00C4D8A8 k13 false ; flag indicating that k11 contains a message to emit
  -   CONST$00C4D8B0 k14 'Faction_SetMinimumRelation' [h=4FB36F98,$00A3EC80]
  -   CONST$00C4D8B8 k15 'allies' [h=B57F1C27,$009A61A0]
      CONST$00C4D8C0 k16 TObject(100.0)
      CONST$00C4D8C8 k17 TObject(-100.0)
  -   CONST$00C4D8D0 k18 'china' [h=1129D14E,$009A6060]
  -   CONST$00C4D8D8 k19 'mafia' [h=11226556,$009A6140]
  -   CONST$00C4D8E0 k20 'sk' [h=00001514,$009A6180]
      CONST$00C4D8E8 k21 '[global.lua] AttemptFactionMoodClamp: within first mission sequence; clamping faction mood\n' [h=7DCC8073,$00A83CC0]
      CONST$00C4D8F0 k22 TObject(59.0)
      CONST$00C4D8F8 k23 TObject(-59.0)
      CONST$00C4D900 k24 '[global.lua] AttemptFactionMoodClamp: beyond first mission sequence; not clamping faction mood\n' [h=6ABD1F45,$00A760C0]

  The desired behaviour, as lua source, is:

      gameflow_ShouldGameStateApply()
      gameflow_AttemptAceMissionUnlock()
      Faction_SetMinimumRelation('allies', <allies floor>)
      Faction_SetMinimumRelation('china', <china floor>)
      Faction_SetMinimumRelation('mafia', <mafia floor>)
      Faction_SetMinimumRelation('sk', <sk floor>)
      if not bDebugOutput then return end
      Player_SetMoney(Player_GetMoney() + <money bonus>)
      if <has_message> then
        Ui_PrintHudMessage(<message>)
      end
      bDebugOutput = not bDebugOutput
      return

  '''
  sgsa_name = globals['gameflow_ShouldGameStateApply_name']
  aamu_name = globals['gameflow_AttemptAceMissionUnlock_name']
  flag_name = globals['bDebugOutput_name']
  setmoney_name = globals['Player_SetMoney_name']
  getmoney_name = globals['Player_GetMoney_name']
  hudmessage_name = globals['Ui_PrintHudMessage_name']

  with globals['AttemptFactionMoodClamp'].val().lock() as f:
    f.setk(0, sgsa_name, tt=LUA_TSTRING) # To be called
    f.setk(1, aamu_name, tt=LUA_TSTRING) # To be called
    f.setk(2, flag_name, tt=LUA_TSTRING) # Idempotency flag
    f.setk(3, setmoney_name, tt=LUA_TSTRING) # To be called
    f.setk(4, getmoney_name, tt=LUA_TSTRING) # To be called
    f.setk(5, -100.0, tt=LUA_TNUMBER) # Mood floors to apply
    f.setk(6, -100.0, tt=LUA_TNUMBER) # allies/china/mafia/SK
    f.setk(7, -100.0, tt=LUA_TNUMBER)
    f.setk(8, -100.0, tt=LUA_TNUMBER)
    f.setk(9, 0.0, tt=LUA_TNUMBER) # Money bonus
    f.setk(10, hudmessage_name, tt=LUA_TSTRING) # To be called
    # f.setk(11, "") # message buffer, will be set by caller as needed
    f.setk(13, False, tt=LUA_TBOOL) # "pending message" flag
    f.patch(0, [
      # 00 <k0> gameflow_ShouldGameStateApply()
      LuaOpcode('GETGLOBAL', A=0, Bx=0),
      LuaOpcode('CALL', A=0, B=1, C=1),
      # 02 <k1> gameflow_AttemptAceMissionUnlock()
      LuaOpcode('GETGLOBAL', A=0, Bx=1),
      LuaOpcode('CALL', A=0, B=1, C=1),
      # 04 <k14> Faction_SetMinimumRelation(<k15> 'allies', <k5> allies floor)
      LuaOpcode('GETGLOBAL', A=0, Bx=14),
      LuaOpcode('LOADK', A=1, Bx=15),
      LuaOpcode('LOADK', A=2, Bx=5),
      LuaOpcode('CALL', A=0, B=3, C=1),
      # 08 <k14> Faction_SetMinimumRelation(<k18> 'china', <k6> china floor)
      LuaOpcode('GETGLOBAL', A=0, Bx=14),
      LuaOpcode('LOADK', A=1, Bx=18),
      LuaOpcode('LOADK', A=2, Bx=6),
      LuaOpcode('CALL', A=0, B=3, C=1),
      # 12 <k14> Faction_SetMinimumRelation(<k19> 'mafia', <k7> mafia floor)
      LuaOpcode('GETGLOBAL', A=0, Bx=14),
      LuaOpcode('LOADK', A=1, Bx=19),
      LuaOpcode('LOADK', A=2, Bx=7),
      LuaOpcode('CALL', A=0, B=3, C=1),
      # 16 <k14> Faction_SetMinimumRelation(<k20> 'sk', <k8> sk floor)
      LuaOpcode('GETGLOBAL', A=0, Bx=14),
      LuaOpcode('LOADK', A=1, Bx=20),
      LuaOpcode('LOADK', A=2, Bx=8),
      LuaOpcode('CALL', A=0, B=3, C=1),
      # 20 if not <k2> bDebugOutput then return end
      LuaOpcode('GETGLOBAL', A=0, Bx=2), # from this moment on we keep bDebugOutput in r0
      LuaOpcode('TEST', C=0, B=0, A=0),
      LuaOpcode('JMP', sBx=(77-23)), # 22, so PC is 23, and end of fn is 77
      # 23 <k3> Player_SetMoney(<k4> Player_GetMoney() + <k9> money bonus)
      # bonus may be zero, hopefully that's a no-op?
      LuaOpcode('GETGLOBAL', A=1, Bx=3), # ... setmoney
      LuaOpcode('GETGLOBAL', A=2, Bx=4), # ... setmoney getmoney
      LuaOpcode('CALL', A=2, B=1, C=2),  # ... setmoney $player
      LuaOpcode('LOADK', A=3, Bx=9),     # ... setmoney $player $bonus
      LuaOpcode('ADD', A=2, B=2, C=3),   # ... setmoney $total
      LuaOpcode('CALL', A=1, B=2, C=1),
      # 29 if not <k13> has_message then return end
      LuaOpcode('LOADK', A=1, Bx=13),
      LuaOpcode('TEST', C=0, B=0, A=0),
      LuaOpcode('JMP', sBx=(77-32)), # 31, so PC is 32
      # 32 <k10> Ui_PrintDebugMessage(<k11> message)
      LuaOpcode('GETGLOBAL', A=1, Bx=10),
      LuaOpcode('LOADK', A=2, Bx=11),
      LuaOpcode('CALL', A=1, B=2, C=1),
      # 35 <k2> bDebugOutput = not bDebugOutput
      LuaOpcode('NOT', A=0, B=0),
      LuaOpcode('SETGLOBAL', A=0, Bx=2),
      # eof
      LuaOpcode('RETURN', B=1),
    ])
