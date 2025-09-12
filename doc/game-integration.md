# Integration with Mercenaries

The way this interfaces with the running game is complicated enough that I felt
it worth documenting here.

In some cases, we can simply read or write memory directly, but in others we're
getting weird with it and injecting lua bytecode and suchlike.


## The main hook into Lua

Since much of the game logic is implemented in Lua, it is convenient to be able
to inject our own Lua code, and call it, both to implement changes and to extract
data from the game. Unfortunately, we have no safe way of directly doing this; we
can neither allocate memory (necessary for creating new functions) nor manipulate
the lua data stack and invoke C functions (necessary for calling those functions)
without a lot more reverse engineering work and a serious risk of memory corruption.

Instead, we repurpose existing functions that either do nothing useful (e.g. debug
print functions that are useless without a serial debugger attached to a dev console)
or have code that we can safely replace (logging statements, game logic that is
superseded by the randomizer).

Changes to individual functions to support specific use cases are documented below;
this section describes the "top-level" hook.

### `ApplyFactionMoodClamp`

This is our main entry point. It is a large function (25 constants, 77 instructions)
but most of it is bookkeeping to figure out where you are in the game, and apply
a mood floor based on that (-59 in the tutorial, -100 otherwise) to all factions.
Since the AP version uses AP items to adjust mood floor, and the logic for that
is contained in the client rather than in the game, we can cut that down to 9
constants and 16 instructions, leaving the other 16/61 free.

Into this function, we can then insert code to call other functions we need (at a cost
of 1 constant and 2 instructions per call); when this document says that a function
is "hooked", this is what it means. We can also simply add bespoke code for any purpose,
if there is no existing function we can make use of.

### `bDebugOutput`

This is used as a deliver-once flag. Some of what we insert into the game, like
money or event messages, needs to be delivered once only, not every time the hooks
are called. To that end, we use this global, which is (in normal play) always present
and always false.

The back half of `ApplyFactionMoodClamp` is used for deliver-once code, and is
skipped entirely if `bDebugOutput` is false:

    [to include the relevant TEST instruction here]

If it is true, that code is executed and the flag reset to false. The AP client
can then see that those items were delivered (by the flag changing from true to
false) and, if needed, insert more items and set the flag to true again.

### `Debug_Printf` and `util_PrintDebugMsg`

These functions are effectively no-ops in the production build, but they are called
*all over the place*. By replacing their entries in `_G` with alternate references
to `ApplyFactionMoodClamp`, we ensure that it -- and thus our hooks -- get called
on a regular basis; generally speaking, moving far enough that parts of the world
need to load/unload or doing something that affects faction reputation is sufficient.


## Sending

This section covers things we need to insert into the game in response to changes
to AP.

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

Discounts are handled entirely AP-side; we hardcode the "base price" of each item
in the AP client, then compute the discounted price based on what items the player
has found and that is what gets written to memory.


### Money

Reading money is easy: `$00558BF0` and `$00558BF0` contain the current and
target amounts displayed on the HUD, as integers, and we can simply read those,
should we need to.

Writing money is harder. It's stored as a float, at offset 0xB60 into a struct
that is dynamically allocated and moves around regularly, and to which stable
pointers are hard to find. So, we bypass this completely and instead do it in
Lua.

Lua exposes three functions for this: `Player_GetMoney`, `Player_SetMoney`, and
`Player_AdjustMoney`. The latter takes a delta and would cost fewer instructions
to call as a result, but also expects a second argument of unclear purpose, and
there is prior art in `challenge_Recycler_Start` demonstrating the validity of
the read-modify-write approach using the former two functions:

    011 010000C5 GETGLOBAL r1 := _G[k3 ('Player_SetMoney' [h=F58D4D46,$00986300])]
    012 02000085 GETGLOBAL r2 := _G[k2 ('Player_GetMoney' [h=21DC1219,$009862E0])]
    013 02008099      CALL r2 (0 args) => 1 results
    014 03003E86  GETTABLE r3 := r0[k0 ('nDeposit' [h=0D68C875,$00988E00])]
    015 020100CD       SUB r2 := r2 - r3
    016 01010059      CALL r1 (1 args) => 0 results

So, we use three constant slots (one for each function and one for the actual
amount of money to be delivered) and six instructions (as above) in the deliver-once
hook code to grant the player money. To deliver money, we simply set the amount-of-money
constant to our desired value, set the delivery flag, and the next time the hooks
run it will appear in their account.


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

This done, all we need to do is hook `gameflow_AttemptAceMissionUnlock` to be called
regularly, instead of only on card verification; once the player has enough intel
they will generally get the ace mission email in under a minute.

N.b. I have not yet figured out how the progress bar in the PDA is computed; it
doesn't seem to be based on `gameflow_GetIntelTotal`.


### Faction reputation floor increases

This is easy because (as discussed earlier) `AttemptFactionMoodClamp` already
does this; we just need to grab four constants from its constant table, one for
each faction, and adjust them as we see fit, and the floors will be adjusted
next time the hooks run. Faction floor settings are idempotent so there are no
concerns about multi-delivery; we just compute the effective floor in the AP client
and inject it.


### Future work

At some point I would also like to add support for:
- one-time faction reputation bonuses
- airstrike coupons
- health/ammo/grenade refills
- hints
  - capturing a number alive can give a hint about a progression item, perhaps?


## Receiving

This section covers things we need to do to extract information from the game,
typically for the purpose of figuring out which checks the player has hit.


### Deck of 52

This is the simplest.

The status for the Two of Clubs is stored at `$005240e4`. The rest of the cards
are stored in the memory that follows, with a spacing of 0x28 bytes, in suit
order clubs-diamonds-hearts-spades, and within each suit, in value order
23456789XJQKA. This means that to get the status of the entire deck we need
only read these 52 bytes of memory.

A value of 1 means they are at large; 2 means killed, and 3 captured.

The one caveat is that card status sometimes does not update until the next time
the player opens their PDA, so there may be a delay before a card verification
becomes visible in memory. We may, in the future, be able to eliminate this
latency by injecting code into `gameflow_DeckCardVerified` instead.

#### Chapter inference

Some features, including telling if the game is completed, depend on knowing what chapter the player is in. For our
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

And now we can easily fish the data out of _G with
`L.getglobal('mission_accepted).val`. The only hazard is that we write a new
`mission_accepted` table every time this is called, which means the old one
becomes subject to garbage collection; we can hold a reference to the table node
but cannot safely hold a reference to the table itself long-term.

We now simply need to call `ShouldGameStateApply`. This is done by hooking it in
the usual manner, but that engenders a new problem: it expects three arguments,
and we don't know what they should be. Fortunately, none of them are needed until
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

This ensures that when called via the hook, it simply produces the table, stores
it in _G, and returns without doing any other work.

N.b. There is a global table, `tCurrentMissions`, which contains exactly the information
we need; however, it doesn't seem to exist reliably. It may nonetheless be useful
if we can be sure it exists often enough.


### Bounty collection

It would be really nice if I could figure out which specific bounties have been
collected, but I have yet to figure that out.

In the meantime, we can get the bounty count by reading some string buffers, which
I believe are used for the PDA display of bounty stats.

To get to them, we first read some offsets from known addresses:

    $0050202A - listening posts
    $00502BE0 - blueprints
    $00502202 - monuments
    $00502294 - treasures

We then add the offset to 0x00da38c0 and that gives us the starting point of a
null terminated string containing the decimal form of the number of bounties of
that type collected.


### Future work

- mission bonus objectives
- challenges
- first time you drive each kind of vehicle
- first time you destroy each kind of vehicle
  - above three can probably be gotten in the same manner as bounties
