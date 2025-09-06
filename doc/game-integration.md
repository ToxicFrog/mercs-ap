# Integration with Mercenaries

The way this interfaces with the running game is complicated enough that I felt
it worth documenting here.

In some cases, we can simply read or write memory directly, but in others we're
getting weird with it and injecting lua bytecode and suchlike.


## Items

These are things we need to write to the game as we receive them from AP.


### Merchant of Menace unlocks

This is one of the easy ones. At `$0051EE7C` there is an array of structs that
look like this:

    00 uint32 tag;
    04 uint32 price;
    08 bool32 new;

Each one corresponds to a MOM unlock and they appear in the order the player has
unlocked them. The `new` tag is used to display the "New!" indicator in the
shop UI. The `tag` denotes which actual item is unlocked; see `shopdata.py`
for a complete list.

Note that the price is here and not in some master template; that means we can
implement discounts (or price hikes) as we see fit.

At `$51F47C` there is some additional metadata:

    51F47C int32 total_unlocked;
    51F480 int32 vehicles;
    51F484 int32 supplies;
    51F488 int32 airstrikes;
    51F48C int32 selection;

`total_unlocked` is the most important one, since that controls how many
elements of the above array are actually considered; the game will read elements
from 0 to `total_unlocked`-1 and ignore the rest. The next three elements are
purely cosmetic and used to draw the scrollbars, and the last is internal
bookkeeping by the UI and will be overwritten.

This means that to remove elements, we swap them into tail position (if
necessary) and decrement `total_unlocked`, and to add elements, we write them at
the tail and then increment `total_unlocked`.


### Money

Reading money is easy: `$00558BF0` and `$00558BF0` contain the current and
target amounts displayed on the HUD, as integers, and we can simply read those.

Writing money is harder. It's stored as a float at offset 0xB60 in a struct
somewhere. The "somewhere" is the hard part; stable pointers to this struct are
hard to find.

The best I've managed so far is `$00558B4C`, which points to it, but only if the
player is on foot. If in a vehicle, it appears to point to the vehicle instead.
Fortunately, there are flags for that at `$00558B10` (true if the player is on
foot) and `$00558B14` (true if the player is driving).

So, to update money, we first read `$00558B10` to check the player's state. If
that's 1, we read `$00558B4C` to get the struct address, add 0xB60 to get the
money field, and then read-modify-write.

TODO: in the future, if we can do this by lua code injection calling
`Player_AdjustMoney()`, that would be much safer.


### Intel

There is no central location where intel total is stored. Instead, every time
the player verifies a card, the game calls `gameflow_AttemptAceMissionUnlock()`
in Lua. This calls `gameflow_GetIntelTotal(chapter)`, which recomputes the intel
total from scratch, and compares the result to `iTargetIntel` (which is 80) to
see if you're ready for the ace.

To handle intel, then, we do two things. The first is patching `GetIntelTotal`
to return whatever we want. The function starts with:

    000 01000001     LOADK r1 := k0 (0.0)
    001 02000045 GETGLOBAL r2 := _G[k1 ('suit_sequence' [h=3E108615,$009A9EE0])]

By replacing instruction 1 with `RETURN r0 ... r0`, we turn it into a function that
returns whatever's in k0 immediately. k0 is, conveniently, already a numeric
constant (0), so by writing to its value slot from outside the game, we directly
control the perceived intel total.

This is not sufficient in itself, however; `AttemptAceMissionUnlock` is called
only when you verify a card, which means you can end up in a state where you
have no actions remaining that will trigger it. We want it to be called
frequently, if possible. Conveniently, there are two functions that are called
very frequently but also do nothing important to gameplay: `Debug_Printf` and
`util_PrintDebugMsg`. By modifying the global hash table entries for these to
instead point to `AttemptAceMissionUnlock`, we guarantee it is frequently called
and the ace mission is unlocked as soon as the player has sufficient intel.


### Future work

At some point I would also like to add support for:
- shop discounts
  - already doable via the unlock array
- faction reputation bonuses
- reputation floor bonuses
  - k-hacking on AttemptFactionMoodClamp
- airstrike coupons
- health/ammo/grenade refills
- hints
  - missions that give number location info can also give hints about what they're carrying
  - capturing a number alive can give a hint about a progression item, perhaps?


## Checks

These are the things the player can do in-game to result in location checks
being sent to AP. Despite only reading and not modifying the game state, this
is not any simpler.


### Deck of 52

Ok, this one actually is simple.

The status for the Two of Clubs is stored at `$005240e4`. The rest of the cards
are stored in the memory that follows, with a spacing of 0x28 bytes, in suit
order clubs-diamonds-hearts-spades, and within each suit, in value order
23456789XJQKA. This means that to get the status of the entire deck we need
only read these 52 bytes of memory.

A value of 1 means they are at large; 2 means killed, and 3 captured.

The one caveat is that card status sometimes does not update until the next time
the player opens their PDA, so there may be a delay before a card verification
becomes visible in memory.

#### Chapter inference

Some future features depend on knowing what chapter the player is in. For our
purposes we can get away with inferring this based on Ace status, since chapter
transitions are always triggered by a mission in which you must verify an Ace.


### Mission completion

This is (like many other things in the game) stored in "scribble memory", which
unfortunately appears to be compressed or encoded somehow -- I suspect it's an
in-RAM copy of what eventually gets saved to or loaded from the memory card. The
canonical mechanism for reading it is the lua functions
`Utility_ReadNumberFromScribbleMemory(key)` and
`Utility_ReadStringFromScribbleMemory(key)`, where the key is a suitable string.

The keys we care about here are `'current_allies_mission'`,
`'current_sk_mission'`, `'current_china_mission'`, and
`'current_mafia_mission'`. Ideally, we'd like to exfiltrate the value of all of
these in one go.

The most promising place for this is `gameflow_ShouldGameStateApply(_, _, _)`,
which not only has all of that data, but conveniently packs it all into a table:

    006 050000CA  NEWTABLE r5 := {} (#a=0, #h=3)
    007 06000005 GETGLOBAL r6 := _G['Utility_ReadNumberFromScribbleMemory' [h=2BB92038,$00A00C80]]
    008 07000141     LOADK r7 := 'current_allies_mission' [h=CB04149F,$009E5800]
    009 06010099      CALL r6 (1 args) => 1 results
    010 057F0189  SETTABLE r6 ->> r5['allies' [h=B57F1C27,$009A61A0]]
    ... more of the same in 11-22

Even better, shortly afterwards, with the table still on the stack, are three
debug instructions we can replace:

    024 07000305 GETGLOBAL r7 := _G[k12 ('util_PrintDebugMsg' [h=A2961C17,$00A11FC0])]
    025 08000341     LOADK r8 := k13 ('\n[gameflow.lua] ...' [h=94811E5E,$00A97F40])
    026 07010059      CALL r7 (1 args) => 0 results

We can only call SETGLOBAL with a string, but conveniently k1 is
`'mission_accepted'`, which is (a) never used as a global anywhere else and (b)
vaguely relevant. So we patch the code accordingly:

    024 05000047 SETGLOBAL r5 ->> _G[k1]
    025 00000000       NOP
    026 00000000       NOP

And now we can easily fish the data out of _G with `L.getglobal(1).val`.

Unfortunately, this requires the function to actually get called, and it looks
like it is in normal play only called during lua VM initialization. So we need
to hook it from `Debug_Printf` and/or `util_PrintDebugMsg`, which we previously
redirected to `gameflow_AttemptAceMissionUnlock`.

There's not much we can do with `AttemptAceMissionUnlock`, but perhaps, instead
of replacing `util_PrintDebugMsg` with a pointer to it, we can rewrite it to
call both `AttemptAceMissionUnlock` and `ShouldGameStateApply`.

It's pretty small, with two constants and six free instructions:

    CONST$009609A0 k0  'bDebugOutput' [h=2660F98C,$009A6CC0]
    CONST$009609A8 k1  'Debug_Printf' [h=445430CF,$0098B6A0]
    CODE $009974E0
      000 01000005 GETGLOBAL r1 := _G[k0 ('bDebugOutput' [h=2660F98C,$009A6CC0])]
      001 01008018      TEST not r1: r1 := r1 ; or skip
      002 00800094       JMP +3 ; 6
      003 01000045 GETGLOBAL r1 := _G[k1 ('Debug_Printf' [h=445430CF,$0098B6A0])]
      004 02000000      MOVE r2 := r0
      005 01010059      CALL r1 (1 args) => 0 results
      006 0000801B    RETURN r0 ... r-1

But it's big enough to work with.

First, we replace the constants with the names of the two functions we want to
call:

    CONST$009609A0 k0  'gameflow_ShouldGameStateApply'
    CONST$009609A8 k1  'gameflow_AttemptAceMissionUnlock'

Then we replace the function body:

    000 00000005 GETGLOBAL r0 := _G[k0]
    001 00008059      CALL r0 (0 args) => 0 results
    002 00000045 GETGLOBAL r0 := _G[k1]
    003 00008059      CALL r0 (0 args) => 0 results
    004 0000801B    RETURN r0 ... r-1

Of course, this produces a new problem: `ShouldGameStateApply` expects 3
arguments and we are providing none. Fortunately, none of them are needed until
after we have exfiltrated the mission completion data, and we have two spare
instructions we can use to replace with an early exit if the first argument is
nil (which should never happen normally, since immediately afterwards it does
an unchecked table index operation on it):

    024 05000047 SETGLOBAL r5 ->> _G[k1]
    025 00000018      TEST not r0 : r0 := r0
    026 00800C54       JMP +50 ; 77

Which is equivalent to the Lua code:

    mission_accepted = { ... }
    if not r0 then return end

Thus allowing us to safely call it with no arguments, in which case it will
save the data we need in _G and then return, doing no other work.


### Future work

- bounties (listening posts, blueprints, treasures, monuments)
  - util_GetBountyName might be useful here? called from nextsw and nextnw
  - references g_iCurrentNwBountyIndex and g_iCurrentSwBountyIndex, neither of
    which are actually defined :/
  - found some useful strings, which don't tell me which ones have been collected
    but do have total counts
- mission bonus objectives
- challenges
- first time you drive each kind of vehicle
- first time you destroy each kind of vehicle
  - above three can probably be gotten in the same manner as bounties

## Money
