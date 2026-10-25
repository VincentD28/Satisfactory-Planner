# Author      : Vincent Dufresne
# Date        : 12-08-2026

# todo : 
#      : 
#      : 
#      : 
#      : brighter on off button
#      : consistent progress bar size
#      : thiner type nodes + bigger text
#      : arrow in hub for output to proj input (for proj input, show all the needed input even before linking them)
#      : cant complete a output node
#      : bug with recipe manager, changing a recipe just add it, not change it
#      : ressource nodes in proj + linking in hub or proj
#      : upgrade bar for instance nodes (rectangular stop for the right of progress bar,at the top, write the name : mk1, mk2, mk3 and at the bottom, the rate, only show the rate of the current bar max, make the info at the top of the instance always fit (ex.: Normal, Miner Mk.1, 100%), not able to change the linking in the instance)
#      : map to connect input for project to the the nodes they are extraction (keeping track of the usage of each nodes)

#      : x Alien Power Augmenter as a generator (plain, or burning Alien Power Matrix): 500 MW each + 10% / 30% of the whole hub grid's power, the grid power going in shown on its card, its node's panel and the power node
#      : x pipeline pumps on fluid lines: hover a pipe and click once to place one (the pipe level's mark), click it for its settings (mark, number, remove), drag it along; a power line to the power node each
#      : x output panel: Output / Power, Power holding Generator / Consumer. A consumer (stations, platforms, locomotive, drone port, hypertube entrance, elevator, lights, sink, radar tower, portals) is a card counted in buildings and a node on the map drawing on the power node

#      : x recipe dropdowns (graph and output cards): Change or Add the recipe picked; an added one takes the flow typed in a box (0 to all of the others', the others giving it up), an output's recipes share one card
#      : x water, oil and resource well extractors say their flow under the node instead of their count, like the miners
#      : x hub cards switch off (power button in the band, or the card menu): faded, power line down, left out of the hub's total (remembered)
#      : x a dragged hub card's shadow no longer left behind on the grid
#      : x the window's own title bar (Windows): taller, in the app's grey, gear + name, its own min/max/close (close goes red), native dragging/snapping/resizing kept
#      : x node titles never cut a word: the name shrinks to the biggest size its longest word fits at, to the pixel
#      : x hub and tabs live both ways: a card dragged on the hub moves the tabs as it goes, a tab dragged moves the cards
#      : x output order in the panel follows the tree only when built with the button (dragged boxes, outline mode, a node's recipe or reopening leave it)
#      : x 5 projects per row in the hub
#      : x the gear app icon on the window (and the taskbar, run from the scripts too)
#      : x game version centered in its tag, by its capitals and figures
#      : x hub cards widen for their outputs, only as much as they need (up to 10 pictures, then "+n"), power lines climb in gaps clear of every card
#      : x title "Satisfactory Planner"
#      : x bigger dashes and gaps (output outlines, the hub's New project card)
#      : x node info: a product going to an output wears its box's outline on its row (green top, dashed green top, dashed teal bottom), in both outputs modes
#      : x color sampler: pipette beside the hex field, freezes every screen and takes the clicked pixel (other apps too; right click / Esc cancels)
#      : x hex field under the color sliders (any color, black included; sliders follow it)
#      : x open tab's name (and close cross) dark on a light tab color, light on a dark one
#      : x name + color changed together in the rename box: confirmed together (Enter / tick), cancelled together (Escape / click away, color put back)
#      : x tab pages: wheel turns a whole page, next/new page button after the "+", page numbers strip over the row (drop a tab on one to move it), all-rows mode button
#      : x tabs as wide as their name (never cut) + names of letters/digits/space/-/_ only + 24 char limit + smaller tabs by default
#      : x compact output view: picture + rate tiles, two to a row, order kept (button in the section heading)
#      : x graph option bar folds down to its corner, full screen kept (remembered)
#      : x option space only as tall as its rows + button to collapse it (remembered)
#      : x below miner extraction node, the number of ore per min instead of the miner count (miner mark kept)
#      : x dragging tabs (along the row) + dragging outputs (up and down their list, by the grip)
#      : x default the rate for one machine output (follows the recipe until the rate is changed)
#      : x allow fraction output with dot
#      : x elec arrow moved to the node's top left, in its line's own green/red
#      : x generator imgs added to img (the power card keeps the bolt)
#      : x app and projects saved to appdata.json: outputs, node positions, options, camera
#      : x recipes feeding each other: a straight run down the column, border to border
#      : x ports re-sort as boxes are dragged, the line easing across to its new one
#      : x generation placement: a build always lays out afresh, add and regenerate agree
#      : x power lines: own landing spot on the node, direction arrows, a color per direction
#      : x collaps button for node info (collapsed by default, button at the node's top right)
#      : x lines of highlighted nodes drawn on top of the others
#      : x byproducts of generator labeled as such if not main goal, placed after the final products layer
#      : x instant color secondary change (more clean)
#      : x default missing img for missing imgs
#      : x powerlines to the graph + power report
#      : x cleaning node expended info
#      : x preemptively changing output recipe
#      : x changing recipe of a node in the graph (recalulating the subtree)
#      : x multiple recipes for an item pn the graph
#      : x recipe byproduct feeding other recipes
#      : x reduce lag (for zooming, moving and playing)
#      :

# === WHAT EVERY NODE CARRIES ===
#
# Node
#   - id
#   - coordinate
#   - layer
#   - mother_nodes
#   - daughter_nodes
#   - ingredients
#   - products
#   - merged_into
#
# Output_Node : Node +
#   - item
#   - rate
#   - is_byproduct
#   - picture
#
# Manual_Node : Node +
#   - item
#   - needed_rate
#   - rate
#   - picture
#
# Power_Node : Node +          every machine's draw, as one node they take from
#   - item                     POWER_ITEM
#   - rate                     the whole factory's draw, in MW
#   - picture                  none: the map draws it a bolt of its own
#
# Recipe_Node : Node +
#   - needed_item
#   - needed_rate
#   - item (property)
#   - possible_recipes
#   - recipe
#   - recipe_name
#   - is_alternate
#   - machine
#   - duration                 the recipe's, or the picked miner's for an extraction
#   - item_picture
#   - machine_picture
#   - machine_nb
#   - full_machines
#   - last_machine_clock
#   - machine_built
#   - needed_power             its draw, also carried as a POWER_ITEM ingredient

import json
import math
import os
from collections import deque
from enum import Enum
from data_maker import Item, Recipe, Machine, PowerBuilding, data_file

# === CLEANED_DATA --> All_... ===

# whichever copy is at hand: one written beside the exe by an update, else
# the one built into it (see data_maker.data_file)
SOURCE_PATH_CLEANED_DATA = data_file("cleaned_data.json")

# Every item, recipe and machine of the game, as data_maker left them. The
# three tables are filled in place rather than replaced, so anything holding
# one of them - every other module does - still sees the whole of the data
# after it has been read again (see reload, which the home page runs when the
# game's own files have moved on).
All_Recipes = {}
All_Items = {}
All_Machines = {}
# ...and every building that only draws power (see data_maker.PowerBuilding):
# the consumers an output panel can ask for, and the pumps a pipe can carry
All_Power_Buildings = {}

MINER_NAME = "Build_MinerMk{}_C"
MINER_MARK = 1

def set_miner_mark(mark):
    global MINER_MARK
    MINER_MARK = mark

# The resource nodes the project being built has assigned to what it digs
# out, by item: [(extractor, rate it gives, rate it gives at 100% clock)], in
# the order they are filled. An extraction box of one of them stands its
# machines on those nodes - one extractor a node - rather than counting
# miners on normal nodes (see Recipe_Node.stand_on_sites). Set by the planner
# before every build.
EXTRACTION_SITES = {}

def set_extraction_sites(sites):
    global EXTRACTION_SITES
    EXTRACTION_SITES = sites or {}


def load_data():
    with open(SOURCE_PATH_CLEANED_DATA, encoding="utf-8") as f:
        raw = json.load(f)

    All_Recipes.clear()
    All_Items.clear()
    All_Machines.clear()
    All_Power_Buildings.clear()
    All_Recipes.update({name: Recipe(**d) for name, d in raw["recipes"].items()})
    All_Items.update({name: Item(**d) for name, d in raw["items"].items()})
    All_Machines.update({name: Machine(**d) for name, d in raw["machines"].items()})
    # none in data made before they were read in: no consumer to offer, no pump
    All_Power_Buildings.update({name: PowerBuilding(**d) for name, d in raw.get("power_buildings", {}).items()})


    # swap each name for the Item it points at
    for recipe in All_Recipes.values():
        for entry in recipe.products + recipe.ingredients:
            entry["item"] = All_Items[entry["item"]]

    for machine in All_Machines.values():
        for entry in machine.ingredients:
            entry["item"] = All_Items[entry["item"]]

    # swap each item's recipe names for the Recipe they point at
    for item in All_Items.values():
        item.recipes = [All_Recipes[name] for name in item.recipes]

    # swap each recipe's machine names for the Machine they point at
    for recipe in All_Recipes.values():
        recipe.machine = [All_Machines[name] for name in recipe.machine]

    # swap each extractor's resource names for the Item they point at
    # (empty on the miners, which means any solid rather than nothing)
    for machine in All_Machines.values():
        machine.allowed_resources = [All_Items[name] for name in machine.allowed_resources]

    # a solid resource comes with one extraction recipe per miner mark - the same
    # ore, only faster each mark. They are folded into one: the Mk.1 recipe stays,
    # carries every miner and the time each one takes (`miner_durations`), and the
    # other marks leave the item's recipes. Which miner runs it is not a recipe
    # choice but the planner's miner mark setting (MINER_MARK, see Recipe_Node).

    for item in All_Items.values():
        miner_recipes = [recipe for recipe in item.recipes
                         if not recipe.ingredients and len(recipe.machine) == 1
                         and recipe.machine[0].full_name.startswith("Build_MinerMk")]
        if len(miner_recipes) < 2:
            continue
        miner_recipes.sort(key=lambda recipe: recipe.machine[0].full_name)
        kept = miner_recipes[0]
        kept.miner_durations = {recipe.machine[0]: recipe.duration for recipe in miner_recipes}
        kept.machine = [recipe.machine[0] for recipe in miner_recipes]
        item.recipes = [recipe for recipe in item.recipes if recipe not in miner_recipes[1:]]
        for recipe in miner_recipes[1:]:
            All_Recipes.pop(recipe.full_name, None)



load_data()

# === Power ===
#
# A machine takes power the way it takes ore, so the tree carries it as one
# more ingredient: every recipe node asks for its draw, and one Power_Node
# answers for all of them. Nothing in the game data makes power yet - no
# generator recipes - so that node is the whole factory's draw added up rather
# than a producer sized by demand. When generators arrive it is the node they
# will feed.
#
# The item itself comes from the cleaned data, where the generators produce it
# (data_maker's power generation recipes). One is made up here only for a data
# file written before those existed.
POWER_ITEM = All_Items.get("Desc_Power_C")
if POWER_ITEM is None:
    POWER_ITEM = Item(id=-1, full_name="Desc_Power_C", display_name="Power", recipes=[], picture="")
    All_Items[POWER_ITEM.full_name] = POWER_ITEM

# The data read again, into the same tables and the same power item: what is
# held elsewhere - a recipe on a card, the power item a link is checked
# against - goes on pointing at something real.
def reload():
    load_data()
    made_again = All_Items.get("Desc_Power_C")
    if made_again is not None and made_again is not POWER_ITEM:
        POWER_ITEM.id = made_again.id
        POWER_ITEM.display_name = made_again.display_name
        POWER_ITEM.picture = made_again.picture
        POWER_ITEM.recipes = made_again.recipes
        All_Items["Desc_Power_C"] = POWER_ITEM
        # ...and every recipe that named the new one points at ours instead
        for recipe in All_Recipes.values():
            for entry in recipe.products + recipe.ingredients:
                if entry["item"] is made_again:
                    entry["item"] = POWER_ITEM

# what one machine of `node` draws: its recipe's own range where it has one -
# the particle accelerator, the converter and the quantum encoder swing over a
# range while crafting and their machines carry no draw of their own - and
# otherwise what the machine itself draws.
def machine_power(node):
    return node.recipe.average_power or node.machine.power_consuption

# what `machine_nb` machines add up to, per megawatt one of them draws. A
# part-clocked last machine draws less than its share: power goes with the
# clock to POWER_EXPONENT.
def power_share(machine_nb):
    full = int(machine_nb)
    return full + (machine_nb - full) ** Machine.POWER_EXPONENT

# the draw of `machine_nb` machines of `node`
def power_for(node, machine_nb):
    return machine_power(node) * power_share(machine_nb)

# the two ends of that draw for a recipe whose own power is a range rather than
# a number - a particle accelerator, a converter, a quantum encoder - which
# swings between them the whole time it crafts. None for a recipe that draws
# the same from one second to the next, which is nearly all of them: what
# power_for gives is then the whole story.
def power_range_for(node, machine_nb):
    recipe = getattr(node, "recipe", None)
    if recipe is None or not recipe.power_max or recipe.power_min == recipe.power_max:
        return None
    share = power_share(machine_nb)
    return recipe.power_min * share, recipe.power_max * share

def is_power_node(node):
    return isinstance(node, Power_Node)

# the buildings an output panel can ask for that only draw power, in the
# order the data offers them - and the pumps, the cheapest first
def consumer_buildings():
    return [building for building in All_Power_Buildings.values() if building.category == "consumer"]

def pump_buildings():
    return sorted((building for building in All_Power_Buildings.values() if building.category == "pump"),
                  key=lambda building: building.power)

# A share of the whole grid's power a generator adds on top of its own - the
# Alien Power Augmenter's. 0 for any other.
def power_boost_of(node):
    return getattr(getattr(node, "recipe", None), "power_boost", 0.0) or 0.0

# What draws power without being part of the tree: the buildings the output
# panel asks for that only draw it, and the pumps along its pipes - each
# {"name", "count", "power"} (power for all `count` of them together). The
# power node takes them in, and is made for them when nothing else draws or
# makes power; with none left, it goes as it would have.
def set_extra_draw(nodes, extra):
    extra = [entry for entry in (extra or []) if entry.get("power", 0) > 0]
    power = next((node for node in nodes if is_power_node(node)), None)
    if power is None:
        if not extra:
            return
        power = Power_Node()
        nodes.append(power)
    power.extra = extra
    refresh_power(nodes)

# a recipe that makes power: a burner, a nuclear plant, a geothermal generator
def is_generator(node):
    return isinstance(node, Recipe_Node) and node.entry_for(node.products, POWER_ITEM) is not None

# links the power node to every machine drawing anything, sized to what they
# draw, and to every generator making any, sized to what it makes - whether or
# not the power was asked for: a generator built for its byproduct still puts
# its megawatts on the grid. Takes the node out again when neither side is
# there. Called wherever the rates settle, so it is right at every step of a
# build.
def refresh_power(nodes):
    drawing = [node for node in nodes
               if isinstance(node, (Recipe_Node, Consumer_Node))
               and node.entry_for(node.ingredients, POWER_ITEM) is not None]
    making = [node for node in nodes if is_generator(node)]
    power = next((node for node in nodes if is_power_node(node)), None)

    # the power node stays for what draws on it from outside the tree too
    # (see set_extra_draw), with nothing in the tree drawing or making any
    if not drawing and not making and not (power is not None and power.extra):
        if power is not None:
            cut_out(nodes, [power])
        return
    if power is None:
        power = Power_Node()
        nodes.append(power)

    # what the machines take out of it: they are its mothers, as any taker is
    taken = power.products[0]["to"]
    for node in list(taken):
        if node not in drawing:
            taken.pop(node)
            if node in power.mother_nodes:
                power.mother_nodes.remove(node)
                node.daughter_nodes.remove(power)
    for node in drawing:
        link(node, power)
        entry = node.entry_for(node.ingredients, POWER_ITEM)
        entry["from"] = {power: entry["rate"]}
        taken[node] = entry["rate"]

    # what the generators put into it: they hang under it, as any supplier does.
    # Nothing else can take power off them, so all of it comes here.
    made = power.ingredients[0]["from"]
    for node in list(made):
        if node not in making:
            made.pop(node)
            if node in power.daughter_nodes:
                power.daughter_nodes.remove(node)
                node.mother_nodes.remove(power)
    for node in making:
        link(power, node)
        entry = node.entry_for(node.products, POWER_ITEM)
        entry["to"] = {power: entry["rate"]}
        made[node] = entry["rate"]
    # what the augmenters among them add to the whole grid, as a share of it:
    # each building its own share (see power_boost_of)
    power.boost_fraction = sum(power_boost_of(node) * node.machine_nb for node in making)
    power.recalculate()

# === Node Logic ===

# float rates: an exact > 0 would call rounding dust a byproduct
BYPRODUCT_TOLERANCE = 1e-9

def link(mother, daughter):
    if daughter in mother.daughter_nodes:
        return
    mother.daughter_nodes.append(daughter)
    daughter.mother_nodes.append(mother)

def is_byproduct(node):
    return getattr(node, "is_byproduct", False)

# the byproduct stops taking anything from that recipe
def unlink_byproduct(byproduct, node):
    for entry in node.products:
        entry["to"].pop(byproduct, None)
    byproduct.ingredients[0]["from"].pop(node, None)
    if node in byproduct.daughter_nodes:
        byproduct.daughter_nodes.remove(node)
        node.mother_nodes.remove(byproduct)

# where a byproduct node sits: one layer above the shallowest recipe feeding
# it, so it hangs just off what makes it.
#
# A generator's waste is the exception. A generator normally stands at layer 0
# with the final products, and its waste one past them - but asking for that
# waste as an output too sinks the generator under it, to layer 1, which would
# leave the surplus it still over produces sharing layer 0 with the outputs
# themselves. What is nobody's goal does not belong in the column of what is,
# so a generator's byproduct is put after the final products wherever its
# generator ended up.
BYPRODUCT_LAYER_AFTER_OUTPUTS = -1   # outputs are layer 0; one past them is -1

def byproduct_layer(feeding):
    if any(is_generator(daughter) for daughter in feeding):
        return BYPRODUCT_LAYER_AFTER_OUTPUTS
    return min(daughter.layer for daughter in feeding) - 1

def drop_byproducts(node):
    for byproduct in [mother for mother in node.mother_nodes if is_byproduct(mother)]:
        unlink_byproduct(byproduct, node)

# every recipe checks what it makes past what its takers ask for, and carries
# that surplus off to a byproduct node - one per item, shared by every recipe
# over producing it: when the item already has one it is linked to, otherwise
# it is created. Byproduct takers are not demand (see Recipe_Node.demands), so
# the surplus is read again from scratch on every call, a share that fell to
# nothing is unlinked, and a byproduct nobody feeds anymore leaves the graph.
#
# Returns whether any byproduct was created, relinked, resized or removed.
def refresh_byproducts(nodes):
    def state():
        return {n: dict(n.ingredients[0]["from"]) for n in nodes if is_byproduct(n)}
    before = state()

    for node in [n for n in nodes if isinstance(n, Recipe_Node)]:
        for entry in node.products:
            item = entry["item"]
            if item is POWER_ITEM:
                continue   # power has the one node at the top, which reports its own spare
            wanted = sum(rate for taker, rate in entry["to"].items() if not is_byproduct(taker))
            surplus = entry["rate"] - wanted
            byproduct = next((n for n in nodes if is_byproduct(n) and n.item == item), None)

            if surplus <= BYPRODUCT_TOLERANCE * max(1, entry["rate"]):
                if byproduct is not None:
                    unlink_byproduct(byproduct, node)
                continue

            if byproduct is None:
                byproduct = Output_Node(item, 0, is_byproduct=True)
                nodes.append(byproduct)
            link(byproduct, node)
            entry["to"][byproduct] = surplus
            byproduct.ingredients[0]["from"][node] = surplus

    for byproduct in [n for n in nodes if is_byproduct(n)]:
        given = byproduct.ingredients[0]["from"]
        if not given:
            nodes.remove(byproduct)
            continue
        byproduct.rate = byproduct.ingredients[0]["rate"] = sum(given.values())
        byproduct.layer = byproduct_layer(byproduct.daughter_nodes)

    after = state()
    if before.keys() != after.keys():
        return True
    return any(before[n].keys() != after[n].keys()
               or any(abs(before[n][d] - rate) > BYPRODUCT_TOLERANCE * max(1, rate)
                      for d, rate in after[n].items())
               for n in after)

# in a step build the byproducts move in a step of their own, after the node
# or merge that changed them. The highlight first travels to the node being
# checked, in a step of its own too - taken back when nothing changes, since
# a snapshot is a copy that nothing else points at yet.
def byproduct_step(nodes, steps, node):
    moved = steps[-1]["focus"] is not node
    if moved:
        steps.append(snapshot(nodes, node))
    refresh_power(nodes)   # the machines that just landed draw as well
    if refresh_byproducts(nodes):
        steps.append(snapshot(nodes, node))
    elif moved:
        steps.pop()

# rebuilds one ingredients/products entry at a new rate while keeping the
# repartition already recorded on it: recalculate throws both lists away and
# makes them again, and who takes what must survive that
def flow_entry(previous, item, rate, key):
    old = next((entry for entry in previous if entry["item"] == item), None)
    entry = {"item": item, "rate": rate, key: old[key] if old else {}}
    # the takers only drawing on what is left over (see take_surplus)
    if old is not None and "surplus" in old:
        entry["surplus"] = old["surplus"]
    return entry

# === Rates ===
#
# A tree's rates are not worked out along it once: a creation loop feeds back
# into itself, and a recipe drawing another's leftovers changes how much that
# one's own suppliers have to make. So every node is sized again, over and over
# across the whole graph, until nothing changes any more - a loop whose recipes
# make more than they use settles on its exact rates.
SOLVE_TOLERANCE = 1e-10
SOLVE_MAX_SWEEPS = 2000
SHORT_TOLERANCE = 1e-7   # an ingredient short or a product spare by less is rounding
SOLVE_RUNAWAY = 1e12     # a size past this is a loop that can never settle

# a supplier `taker` only draws what is spare from, rather than asking it to make more
def is_surplus_taker(made, taker):
    return taker in made.get("surplus", ())

# what `producer` makes of `item` that no one asks of it - its share for byproducts
# included, since byproducts take only what is left over anyway
def spare_of(producer, item, excluding=None):
    made = producer.entry_for(producer.products, item)
    if made is None:
        return 0
    taken = sum(rate for taker, rate in made["to"].items() if taker is not excluding and not is_byproduct(taker))
    return made["rate"] - taken

# `node` asks what it eats of its suppliers: its leftover suppliers first, as
# much as each has spare, then the rest shared among its own suppliers the way
# it was shared before
def push_supply(node):
    for entry in node.ingredients:
        suppliers = entry["from"]
        if not suppliers:
            continue
        item, left = entry["item"], entry["rate"]
        primaries = []
        for supplier in list(suppliers):
            made = supplier.entry_for(supplier.products, item)
            if made is None:
                continue
            if is_surplus_taker(made, node):
                take = max(0.0, min(left, spare_of(supplier, item, excluding=node)))
                suppliers[supplier] = made["to"][node] = take
                left -= take
            else:
                primaries.append((supplier, made))
        supplied = sum(suppliers[supplier] for supplier, _ in primaries)
        for supplier, made in primaries:
            share = suppliers[supplier] / supplied if supplied > SOLVE_TOLERANCE else 1 / len(primaries)
            suppliers[supplier] = made["to"][node] = max(0.0, left) * share

def solve_rates(nodes):
    def sizes():
        return [getattr(node, "machine_nb", getattr(node, "rate", 0)) for node in nodes]

    before = sizes()
    for _ in range(SOLVE_MAX_SWEEPS):
        for node in nodes:
            if isinstance(node, Output_Node):
                continue   # an output asks a fixed rate, nothing moves it
            node.recalculate()
            push_supply(node)
        after = sizes()
        if all(abs(a - b) <= SOLVE_TOLERANCE * max(1, abs(a)) for a, b in zip(after, before)):
            refresh_power(nodes)   # the machines are sized: so is their draw
            return
        # a loop using more than it makes never settles: stop before the
        # numbers run off to infinity
        if max(after, default=0) > SOLVE_RUNAWAY:
            refresh_power(nodes)
            return
        before = after

# links `node` to every producer already making `item` spare, as a taker of
# that spare only, up to `rate`. Returns how much it could take.
#
# `node` itself counts as one of those producers: a recipe that gives back some
# of what it takes - Encased Uranium Cell hands back a quarter of its sulfuric
# acid - feeds that straight into its own demand rather than sending it off to
# a byproduct node and asking a supplier for the whole amount. The line it
# makes runs from the node back into itself, and the map draws it as the loop
# under the box. What it keeps for itself is not demand (it is a surplus taker,
# see is_surplus_taker), so it never sizes the machine by its own leftovers.
def take_surplus(node, item, rate, nodes):
    entry = node.entry_for(node.ingredients, item)
    taken = 0
    for producer in nodes:
        if (not isinstance(producer, Recipe_Node)
                or producer in entry["from"] or rate - taken <= SHORT_TOLERANCE * max(1, rate)):
            continue
        made = producer.entry_for(producer.products, item)
        if made is None:
            continue
        spare = spare_of(producer, item)
        if spare <= SHORT_TOLERANCE * max(1, made["rate"]):
            continue
        take = min(rate - taken, spare)
        link(node, producer)
        entry["from"][producer] = take
        made["to"][node] = take
        made.setdefault("surplus", set()).add(node)
        taken += take
    return taken

# A recipe pick, as the choices hold it: one Recipe (or None, the item's
# default), or the item shared between several - [(Recipe, share)], the
# shares adding up to one. Read as the list either way.
def split_of(pick):
    if not isinstance(pick, (list, tuple)):
        return [(pick, 1.0)]
    total = sum(share for _, share in pick)
    if total <= SOLVE_TOLERANCE:
        return [(pick[0][0], 1.0)] if pick else [(None, 1.0)]
    return [(recipe, share / total) for recipe, share in pick]

# ...and back: one recipe when it runs alone, the list when there are several
def pick_of(split):
    split = [(recipe, share) for recipe, share in split if share > SHORT_TOLERANCE]
    merged = {}
    for recipe, share in split:
        merged[recipe] = merged.get(recipe, 0) + share
    if len(merged) == 1:
        return next(iter(merged))
    return [(recipe, share) for recipe, share in merged.items()]

# A fluid in its can or its tank - Packaged Water, Packaged Fuel, ... It is
# always brought in by hand, never made where it is used: a factory taking a
# packaged fluid takes it as it arrives, by train or by truck, packed where
# the fluid is. Packing it on the spot from the fluid the same factory would
# have to pipe in anyway says nothing - and only feeds an unpackager the cans
# it hands back. So the cans an unpackager gives back go nowhere, and leave
# as a byproduct. Asked for as an output, it is made all the same.
PACKAGED_PREFIX = "Packaged "

def is_packaged(item):
    return item.display_name.startswith(PACKAGED_PREFIX)

# Who takes `item` from `target`, and who each of them gets it from: [(taker,
# {supplier: flow})], every supplier of that item into the taker - `target`
# among them - but the ones only handing over their leftovers. A byproduct
# only takes what is spare, and the power node is fed by generators alone, so
# neither is a taker here.
def primary_supply(target, item):
    made = target.entry_for(target.products, item)
    if made is None:
        return []
    takers = []
    for mother in made["to"]:
        if (is_byproduct(mother) or is_power_node(mother) or mother is target
                or is_surplus_taker(made, mother)):
            continue
        suppliers = {}
        if isinstance(mother, Output_Node):
            # an output keeps no record of who supplies it: it is read off
            # every recipe delivering into it
            for daughter in mother.daughter_nodes:
                entry = daughter.entry_for(daughter.products, item)
                if entry is not None and mother in entry["to"] and not is_surplus_taker(entry, mother):
                    suppliers[daughter] = entry["to"][mother]
        else:
            entry = mother.entry_for(mother.ingredients, item)
            for supplier, flow in entry["from"].items():
                given = supplier.entry_for(supplier.products, item)
                if given is not None and not is_surplus_taker(given, mother):
                    suppliers[supplier] = flow
        takers.append((mother, suppliers))
    return takers

# Every machine of `nodes` taking `item` from a recipe of its own - the
# outputs left out, which their cards answer for - and who it gets it from,
# leftovers aside: [(taker, {supplier: flow})]. What the recipe manager of an
# item works on.
def inner_supply(nodes, item):
    takers = []
    for node in nodes:
        if not isinstance(node, Recipe_Node) or node.merged_into is not None:
            continue
        entry = node.entry_for(node.ingredients, item)
        if entry is None:
            continue
        suppliers = {}
        for supplier, flow in entry["from"].items():
            given = supplier.entry_for(supplier.products, item)
            if (isinstance(supplier, Recipe_Node) and supplier is not node and given is not None
                    and not is_surplus_taker(given, node)):
                suppliers[supplier] = flow
        if suppliers:
            takers.append((node, suppliers))
    return takers

# every ingredient still made by a supplier of its own, linked to whatever
# other recipe makes that item spare. Returns whether any link was made.
def use_surplus(nodes):
    linked = False
    for node in [n for n in nodes if isinstance(n, Recipe_Node)]:
        for entry in node.ingredients:
            if entry["item"] is POWER_ITEM:
                continue
            if entry["from"] and take_surplus(node, entry["item"], entry["rate"], nodes):
                linked = True
    return linked

# (node, item, rate) for every ingredient its suppliers fall short on - one
# left drawing only on leftovers, when those leftovers shrank
def shortages(nodes):
    short = []
    for node in [n for n in nodes if isinstance(n, Recipe_Node)]:
        for entry in node.ingredients:
            if entry["item"] is POWER_ITEM:
                continue   # the power node answers for all of it (refresh_power)
            missing = entry["rate"] - sum(entry["from"].values())
            if missing > SHORT_TOLERANCE * max(1, entry["rate"]):
                short.append((node, entry["item"], missing))
    return short

# takes `removed` out of the graph, every link to what stays undone. Returns
# the nodes left supplying nothing to one of them.
def cut_out(nodes, removed):
    gone = set(removed)
    short = set()
    for node in removed:
        drop_byproducts(node)
    for node in removed:
        for mother in node.mother_nodes:
            if mother not in gone:
                mother.daughter_nodes.remove(node)
                for entry in mother.ingredients:
                    entry["from"].pop(node, None)
        for daughter in node.daughter_nodes:
            if daughter not in gone:
                daughter.mother_nodes.remove(node)
                for entry in daughter.products:
                    entry["to"].pop(node, None)
                    entry.get("surplus", set()).discard(node)
                short.add(daughter)
        nodes.remove(node)
    return short

# recipes sized down to nothing - everything they were for is made some other
# way now, a leftover most often - and hand sources no longer asked for
def idle_nodes(nodes):
    return [node for node in nodes
            if (isinstance(node, Recipe_Node) and node.machine_nb <= SHORT_TOLERANCE)
            or (isinstance(node, Manual_Node) and node.rate <= SHORT_TOLERANCE)]

# what crosses one link: a merged producer feeds different mothers different
# items, so it is read off the producer's own repartition
def flow_between(mother, daughter):
    for entry in daughter.products:
        if mother in entry["to"]:
            return entry["item"], entry["to"][mother]
    return daughter.item, 0

# one step of a build: the nodes in the graph at that moment, how they were
# wired, and the numbers they were carrying. The build goes on changing those
# node objects afterwards - a merge rewires them, a recalculate renumbers them -
# so a step that means to show a moment has to copy out of them, not point at
# them. Only the node objects themselves are shared, for their identity.
# `focus` is the mother whose children are being made at that moment, for the
# step viewer to highlight - None before any of them is.
def snapshot(nodes, focus=None):
    present = set(nodes)
    links = []
    for node in nodes:
        for mother in node.mother_nodes:
            if mother in present:
                item, rate = flow_between(mother, node)
                links.append((mother, node, item, rate))
    return {
        "nodes": list(nodes),
        "links": links,
        "values": {node: {"machine_nb": getattr(node, "machine_nb", 0),
                          "rate": getattr(node, "rate", 0),
                          "needed_rate": getattr(node, "needed_rate", 0)}
                   for node in nodes},
        "focus": focus,
    }

# every node's layer, worked out again on the finished graph. A node sits one
# layer under its deepest consumer - but a creation loop (a recipe needing,
# however far down, what it makes itself) has no deepest end to hang from, and
# the build's pushing down only stops because it gives up. So the nodes of
# each loop - each set that can all reach one another through their
# ingredients - are taken as one: the whole loop sits one layer under the
# deepest consumer outside it, all its nodes in that same layer. Everything
# under the loop hangs from it in turn. A graph without a loop comes out with
# the layers it always had. Byproducts, which hang off their recipes rather
# than feed anything, stay one layer above the shallowest recipe feeding them.
def level_layers(nodes):
    present = set(nodes)
    # the power node hangs over the whole graph rather than under a consumer,
    # so it is left out of the layering altogether (the map places it itself)
    crafted = [node for node in nodes if not is_byproduct(node) and not is_power_node(node)]
    feeds = {node: [d for d in node.daughter_nodes
                    if d in present and not is_byproduct(d) and not is_power_node(d)]
             for node in crafted}

    # Tarjan's strongly connected components: each loop, and each node that is
    # in no loop, as one component. They come out sinks first, so reversed
    # they are in order from the outputs down.
    index, low, on_stack, stack, components = {}, {}, set(), [], []

    def strongconnect(node):
        index[node] = low[node] = len(index)
        stack.append(node)
        on_stack.add(node)
        for daughter in feeds[node]:
            if daughter not in index:
                strongconnect(daughter)
                low[node] = min(low[node], low[daughter])
            elif daughter in on_stack:
                low[node] = min(low[node], index[daughter])
        if low[node] == index[node]:
            component = []
            while True:
                member = stack.pop()
                on_stack.discard(member)
                component.append(member)
                if member is node:
                    break
            components.append(component)

    for node in crafted:
        if node not in index:
            strongconnect(node)

    component_of = {member: i for i, component in enumerate(components) for member in component}
    layer_of = {}
    for i in reversed(range(len(components))):
        members = components[i]
        # the power node is no one's consumer for layering: a generator hangs
        # under it, but it rides over the whole map rather than in a column
        consumers = [mother for member in members for mother in member.mother_nodes
                     if mother in present and not is_byproduct(mother) and not is_power_node(mother)
                     and component_of[mother] != i]
        layer_of[i] = max((layer_of[component_of[mother]] + 1 for mother in consumers), default=0)
        for member in members:
            member.layer = layer_of[i]

    for byproduct in [node for node in nodes if is_byproduct(node)]:
        feeding = [d for d in byproduct.daughter_nodes if d in present]
        if feeding:
            byproduct.layer = byproduct_layer(feeding)

# if the recipe created already existe,
# merge the two rate of required item,
# recalculate the number of recipe needed,
# redistribute the output to the parent nodes
# output items that are over produced will create an byproduct node
#
# A merge costs a step, and the node that survives is returned - the new one
# when nothing was running that recipe yet, the twin when it was folded in.

# merge should keep the layer (and pos) of the deepest, 
# update the "to" and recalculate the subtree it create
def merge_if_needed(recipe_node, recipes, nodes, steps, focus=None):
    twin = recipes.get(recipe_node.recipe)
    if twin is None:
        recipes[recipe_node.recipe] = recipe_node
        byproduct_step(nodes, steps, recipe_node)
        return recipe_node

    duplicate = recipe_node

    # merge the two rate of required item. What the duplicate over produced is
    # not carried over: the twin works its own surplus out once resized
    drop_byproducts(duplicate)
    for entry in duplicate.products:
        for parent, rate in entry["to"].items():
            twin.deliver(entry["item"], parent, rate)
            # a parent that drew only the twin's leftovers now asks it for real
            made = twin.entry_for(twin.products, entry["item"])
            made.get("surplus", set()).discard(parent)

    # redistribute the output to the parent nodes: the duplicate's parents
    # take from the twin instead, and it leaves the graph
    for parent in list(duplicate.mother_nodes):
        parent.daughter_nodes.remove(duplicate)
        for entry in parent.ingredients:
            if duplicate in entry["from"]:
                supplied = entry["from"].pop(duplicate)
                entry["from"][twin] = entry["from"].get(twin, 0) + supplied
        link(parent, twin)
    duplicate.mother_nodes.clear()
    duplicate.merged_into = twin
    nodes.remove(duplicate)

    # the twin keeps whichever of the two sat deeper, and the spot that went
    # with it: it now answers to both sets of parents, and has to stay under
    # the lowest of them
    if duplicate.layer > twin.layer:
        twin.layer = duplicate.layer
        twin.coordinate = duplicate.coordinate

    # recalculate the number of recipe needed - and with it anything already
    # built, which was sized against the demand before this merge
    solve_rates(nodes)
    steps.append(snapshot(nodes, focus))

    # output items that are over produced go to a byproduct node - the twin's,
    # and those of anything resized underneath it
    byproduct_step(nodes, steps, twin)
    return twin

class Node():
    _next_id = 1

    def __init__(self, mother_nodes=None):
        self.id = Node._next_id
        Node._next_id += 1
        self.coordinate = (0, 0)
        self.layer = 0
        self.mother_nodes = []
        self.daughter_nodes = []
        # each entry carries its total rate and the repartition of it over the
        # nodes on the other end - who supplies an ingredient, who takes a
        # product. [{"item": Item, "rate": /min, "from"/"to": {node: /min}}]
        self.ingredients = []
        self.products = []
        # set when this node was folded into another: it is gone from the
        # graph, but the steps taken before that still hold it
        self.merged_into = None
        for mother in mother_nodes or []:
            link(mother, self)

    def recalculate(self):
        pass

    def entry_for(self, flows, item):
        return next((entry for entry in flows if entry["item"] == item), None)

    # `mother` takes `rate` of `item` out of this node
    def deliver(self, item, mother, rate):
        takers = self.entry_for(self.products, item)["to"]
        takers[mother] = takers.get(mother, 0) + rate

    # `daughter` supplies `rate` of `item` into this node
    def supply(self, item, daughter, rate):
        givers = self.entry_for(self.ingredients, item)["from"]
        givers[daughter] = givers.get(daughter, 0) + rate

    # the tree for `outputs`, built one piece at a time: the list of steps,
    # each a snapshot of the graph at that moment, the last one the finished tree.
    # An output may name the recipe that makes it ({"item", "rate", "recipe"});
    # without one its item's default recipe is used. `recipe_choices`
    # ({Item: Recipe}) picks the recipe every other node making that item runs.
    # `node_choices` ({(Item, mother's Recipe): Recipe}) picks it for just the
    # nodes making that item for a machine running that recipe, over the other.
    # `extra_draw` is what draws power from outside the tree (see set_extra_draw).
    # `consumers` is the buildings that only draw power, [(PowerBuilding,
    # count)]: a node each, drawing on the power node like any machine.
    @staticmethod
    def get_nodes_from_outputs(outputs, recipe_choices=None, node_choices=None, extra_draw=None, consumers=None):
        build = Build([], [], recipe_choices, node_choices)
        if extra_draw:
            set_extra_draw(build.nodes, extra_draw)
            build.steps.append(snapshot(build.nodes))
        for building, count in consumers or ():
            if building is not None and count > 0:
                build.nodes.append(Consumer_Node(building, count))
        if any(isinstance(node, Consumer_Node) for node in build.nodes):
            refresh_power(build.nodes)
            build.steps.append(snapshot(build.nodes))

        # Loop 0, add the output nodes - one per item, however many outputs ask
        # for it: an item wanted twice, each time from a different recipe, is
        # the one node both recipes deliver into, for the whole rate asked.
        # Power is asked of the power node itself rather than of an output of
        # its own: it is where the generators feed and the machines draw, so
        # the map has one place that says what the factory makes and takes.
        wanted = []   # (output node, rate, recipe) per output asked for
        for output in outputs:
            if output["item"] is POWER_ITEM:
                node = next((n for n in build.nodes if is_power_node(n)), None)
                if node is None:
                    node = Power_Node()
                    build.nodes.append(node)
                    build.steps.append(snapshot(build.nodes))
                node.needed_rate += output["rate"]
                node.ingredients[0]["rate"] = node.needed_rate
                wanted.append((node, output["rate"], output.get("recipe")))
                continue
            node = next((n for n in build.nodes if n.item is output["item"]), None)
            if node is None:
                node = Output_Node(output["item"], output["rate"])
                build.nodes.append(node)
                build.steps.append(snapshot(build.nodes))
            else:
                node.rate += output["rate"]
                node.ingredients[0]["rate"] = node.rate
            wanted.append((node, output["rate"], output.get("recipe")))

        # Loop 1, make the full tree for an output before passing to the next one
        for output_node, rate, recipe in wanted:
            build.focus_on(output_node)
            build.grow(output_node, output_node.item, rate, recipe)

        return build.finish()

    # the finished tree `nodes` (a build's last step) with one node switched to
    # `recipe`: everything only that node's recipe needed - what cannot be
    # reached from an output any more once the node is gone - leaves, what it
    # shared with the rest of the tree is resized to the demand left, and the
    # node is made again under its consumers with the new recipe, its subtree
    # growing step by step as a build does. Everything else is left as it is.
    #
    # Returns (steps, removed): the steps from the tree as it stood to the new
    # one, and the nodes that left.
    @staticmethod
    def rebuild_subtree(nodes, target, recipe, recipe_choices=None, node_choices=None):
        nodes = list(nodes)
        steps = [snapshot(nodes, target)]

        # What the rest of the tree still reaches with the node taken out. The
        # power node counts as an output of its own: megawatts are asked of it
        # rather than of an Output_Node, and every generator hangs under it. A
        # walk that starts only at the outputs cuts the whole power side away,
        # and the generators are then made again sized by whatever else they
        # happen to supply - a fraction of the power that was asked for, taking
        # the rest of the tree down with them.
        reached = set()
        stack = [node for node in nodes
                 if (isinstance(node, Output_Node) and not node.is_byproduct)
                 or (is_power_node(node) and node.needed_rate > 0)
                 or isinstance(node, Consumer_Node)]
        while stack:
            node = stack.pop()
            if node in reached or node is target:
                continue
            reached.add(node)
            stack.extend(node.daughter_nodes)
        removed = [node for node in nodes if node not in reached and not is_byproduct(node)]

        # who asked what of the node, to be supplied again by its new self. One
        # only drawing its leftovers finds them elsewhere, or is supplied anew,
        # once the build finishes.
        takers = [(mother, entry["item"], rate) for entry in target.products
                  for mother, rate in entry["to"].items()
                  if mother in reached and not is_surplus_taker(entry, mother)]

        # cut the subtree out; what it shared is sized down to the demand left
        cut_out(nodes, removed)
        solve_rates(nodes)
        refresh_byproducts(nodes)
        steps.append(snapshot(nodes, takers[0][0] if takers else None))

        # made again, one taker at a time, merging the way a build does
        build = Build(nodes, steps, recipe_choices, node_choices)
        # the new recipe takes over everything it makes; whatever else the node
        # used to supply is made the usual way, by its item's own recipe
        makes = [entry["item"] for entry in recipe.products]
        for mother, item, rate in takers:
            build.focus_on(mother)
            if item in makes:
                build.grow(mother, item, rate, recipe, from_surplus=False)
            else:
                build.grow(mother, item, rate)
        return build.finish(), removed

    # the finished tree `nodes` with `recipe` run beside `target` rather than
    # in its place: of every item the new recipe makes that `target` supplies,
    # `share` of what each of its takers gets from all its suppliers is now
    # made the new way - the suppliers it had, `target` among them, each
    # giving up that share of what they hand it - and the new recipe's node is
    # made under those takers, its subtree growing step by step as a build
    # does. A supplier left making nothing leaves with what only it needed.
    #
    # Returns the steps from the tree as it stood to the new one.
    @staticmethod
    def add_recipe(nodes, target, recipe, share, recipe_choices=None, node_choices=None):
        nodes = list(nodes)
        steps = [snapshot(nodes, target)]
        share = min(max(share, 0.0), 1.0)
        makes = [entry["item"] for entry in recipe.products]
        build = Build(nodes, steps, recipe_choices, node_choices)
        for item in [entry["item"] for entry in target.products if entry["item"] in makes]:
            for mother, suppliers in primary_supply(target, item):
                # Each taker's suppliers are cut down right before its new
                # supplier is written in, never all of them first: sizing the
                # graph between the two - which any merge does - would stretch
                # the cut suppliers back up to all the taker asks for.
                total = sum(suppliers.values())
                for supplier, flow in suppliers.items():
                    kept = flow * (1 - share)
                    supplier.entry_for(supplier.products, item)["to"][mother] = kept
                    if not isinstance(mother, Output_Node):
                        mother.entry_for(mother.ingredients, item)["from"][supplier] = kept
                if total * share <= SHORT_TOLERANCE * max(1, total):
                    continue
                build.focus_on(mother)
                build.grow(mother, item, total * share, recipe, from_surplus=False)
        return build.finish()

    # the finished tree `nodes` with `item` made for every machine taking it
    # (see inner_supply) the way `split` says - [(Recipe, share)], or one
    # Recipe: each recipe of it making that share of what each of them takes.
    # A recipe already supplying a machine has its flow set, a new one is
    # grown under it the way a build does, and one left out of `split` makes
    # it nothing more - leaving with what only it needed.
    #
    # Returns the steps from the tree as it stood to the new one.
    @staticmethod
    def resplit(nodes, item, split, recipe_choices=None, node_choices=None):
        nodes = list(nodes)
        wanted = dict(split_of(split))
        takers = inner_supply(nodes, item)
        steps = [snapshot(nodes, takers[0][0] if takers else None)]
        build = Build(nodes, steps, recipe_choices, node_choices)
        for mother, suppliers in takers:
            # set right before the new suppliers are written in, never all at
            # once first (see add_recipe)
            total = sum(suppliers.values())
            running = set()
            for supplier, flow in suppliers.items():
                kept = total * wanted.get(supplier.recipe, 0.0)
                supplier.entry_for(supplier.products, item)["to"][mother] = kept
                mother.entry_for(mother.ingredients, item)["from"][supplier] = kept
                running.add(supplier.recipe)
            for recipe, share in wanted.items():
                if recipe in running or total * share <= SHORT_TOLERANCE * max(1, total):
                    continue
                build.focus_on(mother)
                build.grow(mother, item, total * share, recipe, from_surplus=False)
        return build.finish()

# one build in progress: the nodes, the steps recorded so far, and the recipe
# each node already runs, for later ones of the same recipe to merge into
class Build:
    def __init__(self, nodes, steps, recipe_choices=None, node_choices=None):
        self.nodes = nodes
        self.steps = steps
        self.recipe_choices = recipe_choices or {}
        self.node_choices = node_choices or {}
        self.recipes = {node.recipe: node for node in nodes
                        if isinstance(node, Recipe_Node) and node.merged_into is None}
        # the mother whose children are being made. Moving it to another node is
        # a step of its own, so the highlight visibly travels before anything
        # new appears under it. It is compared with what the last step shows:
        # checking a node's byproducts lends the highlight to that node, and it
        # has to travel back before the next child is made.
        self.focus = None

    def focus_on(self, mother):
        self.focus = mother
        if not self.steps or self.steps[-1]["focus"] is not mother:
            self.steps.append(snapshot(self.nodes, mother))

    # the recipes picked for `item` made for `mother`, as a split (see
    # split_of): for that node alone first, then for every node making the
    # item; None is the item's default
    def pick(self, item, mother):
        chosen = getattr(mother, "recipe", None)
        return split_of(self.node_choices.get((item, chosen)) or self.recipe_choices.get(item))

    # `rate` of `item` for `mother`, then everything under what makes it,
    # layer by layer. The queue grows while it is walked: that is what carries
    # this subtree down before the next one is started.
    #
    # `recipe` is the recipe to make it with; without one an output's item
    # takes its default, anything else the recipes picked for it (see pick).
    def grow(self, mother, item, rate, recipe=None, from_surplus=True):
        if recipe is None and not isinstance(mother, Output_Node):
            split = self.pick(item, mother)
        else:
            split = [(recipe, 1.0)]
        queue = self.add_supplier(mother, item, rate, split, from_surplus)
        for node in queue:
            for made in [entry["item"] for entry in node.recipe.ingredients]:
                # read again each time: every merge resizes the whole graph
                entry = node.entry_for(node.ingredients, made)
                missing = entry["rate"] - sum(entry["from"].values())
                if missing <= SHORT_TOLERANCE * max(1, entry["rate"]):
                    continue
                self.focus_on(node)
                queue.extend(self.add_supplier(node, made, missing, self.pick(made, node)))

    # suppliers more for `rate` of `item` into `node`: what other recipes
    # make of it spare first (unless `from_surplus` is off), then a hand source
    # when nothing crafts it, or a recipe node per recipe of `split` ([(Recipe,
    # share)]), each for its share - merged into the one already running that
    # recipe when there is one. Returns the new recipe nodes that stay, for
    # their own ingredients to be supplied.
    def add_supplier(self, node, item, rate, split=((None, 1.0),), from_surplus=True):
        nodes, steps = self.nodes, self.steps
        if from_surplus and not isinstance(node, Output_Node):
            taken = take_surplus(node, item, rate, nodes)
            if taken:
                solve_rates(nodes)
                refresh_byproducts(nodes)
                steps.append(snapshot(nodes, self.focus))
                entry = node.entry_for(node.ingredients, item)
                rate = entry["rate"] - sum(entry["from"].values())
                if rate <= SHORT_TOLERANCE * max(1, entry["rate"]):
                    return []

        # nothing crafts it - or it comes packaged, brought in by hand for
        # any machine taking it (see is_packaged): a source, and the end of
        # this branch
        if not item.recipes or (is_packaged(item) and not isinstance(node, Output_Node)):
            source = Manual_Node([node], item, rate)
            source.layer = node.layer + 1
            source.deliver(item, node, rate)
            node.supply(item, source, rate)
            nodes.append(source)
            steps.append(snapshot(nodes, self.focus))
            return []

        # Every share is written in as supplying `node` before any of them
        # merges: a merge sizes the whole graph again, and a node short of
        # what it asks for has its suppliers' shares stretched to cover all of
        # it - the first recipe would take the whole flow, and the split be lost.
        children = []
        for recipe, share in split:
            if share * rate <= SHORT_TOLERANCE * max(1, rate):
                continue
            child = Recipe_Node([node], item, rate * share, recipe=recipe)
            child.layer = node.layer + 1
            if not isinstance(node, Output_Node):
                node.supply(item, child, rate * share)
            nodes.append(child)
            steps.append(snapshot(nodes, self.focus))
            children.append(child)
        # a node that merged away is not queued - the twin it became already
        # has its subtree, resized to the demand the merge added
        return [child for child in children
                if merge_if_needed(child, self.recipes, nodes, steps, self.focus) is child]

    def finish(self):
        nodes, steps = self.nodes, self.steps
        # the whole graph settled: leftovers a recipe made after an ingredient
        # got a supplier of its own are drawn on now, and anything left short
        # by leftovers that shrank gets a supplier - until neither happens
        for _ in range(len(nodes) + 10):
            solve_rates(nodes)
            if use_surplus(nodes):
                solve_rates(nodes)
                refresh_byproducts(nodes)
                steps.append(snapshot(nodes, self.focus))
                continue
            short = shortages(nodes)
            if not short:
                break
            for node, item, missing in short:
                self.focus_on(node)
                self.grow(node, item, missing)

        # what leftovers made unneeded leaves, in a step of its own
        idle = idle_nodes(nodes)
        while idle:
            for node in idle:
                self.recipes.pop(getattr(node, "recipe", None), None)
            cut_out(nodes, idle)
            solve_rates(nodes)
            idle = idle_nodes(nodes)
            refresh_byproducts(nodes)
            steps.append(snapshot(nodes, self.focus))

        # The leftovers read once more off the settled rates, in a step of
        # their own if they moved. A byproduct is read whenever a node or a
        # merge lands, against the rates as they stand then - and a change to
        # a tree already built (a recipe switched, a share moved to another
        # recipe) hands a node less to make before it has been resized to it:
        # what it made for the old share was booked as surplus, and stayed.
        solve_rates(nodes)
        if refresh_byproducts(nodes):
            steps.append(snapshot(nodes, self.focus))

        # the highlight comes off in a step of its own, the mirror of the one
        # that put it on the first mother, so the finished graph ends unmarked
        self.focus_on(None)

        # the layers the build pushed around as it went are settled once and
        # for all on the finished graph - a creation loop's nodes side by side
        level_layers(nodes)
        return steps

# what it takes to build the factory `nodes` describe (a finished build's
# nodes): how many buildings of each machine go up, and every part those
# buildings cost, added up. A recipe running 1.5 machines puts up two
# buildings (machine_built), and it is buildings that cost parts.
# Returns ({Machine: buildings}, {Item: amount}), each most first.
def construction_report(nodes):
    machines = {}
    for node in nodes:
        if isinstance(node, Recipe_Node) and node.machine_built:
            machines[node.machine] = machines.get(node.machine, 0) + node.machine_built

    materials = {}
    for machine, count in machines.items():
        for entry in machine.ingredients:
            materials[entry["item"]] = materials.get(entry["item"], 0) + entry["amount"] * count

    def most_first(counts, name):
        return dict(sorted(counts.items(), key=lambda pair: (-pair[1], name(pair[0]))))

    return (most_first(machines, lambda machine: machine.display_name),
            most_first(materials, lambda item: item.display_name))

# every recipe a finished build runs, in the order the tree reads - from the
# outputs down to what is extracted. One entry per recipe (a merged recipe is
# one node already), each [recipe, machine, machines it runs, layer, item it is
# run for, the items it delivers straight into an output, whether other machines
# take from it too, the first node running it, the items it supplies], its
# machines added up
# should a recipe ever run in more than one node.
# everything a node is asked for, byproducts aside: a recipe making several
# items answers for each of them, not only for the one it is sized on
def supplied_items(node):
    return [entry["item"] for entry in node.products
            if any(not is_byproduct(taker) for taker in entry["to"])] or [node.needed_item]

def recipes_report(nodes):
    entries = {}
    outputs = [node for node in nodes if isinstance(node, Output_Node) and not node.is_byproduct]
    for node in nodes:
        if not isinstance(node, Recipe_Node) or node.merged_into is not None:
            continue
        # the outputs, by their order, this recipe makes directly
        fed = [entry["item"] for entry in node.products
               if any(taker in outputs for taker in entry["to"])]
        inside = any(not isinstance(mother, Output_Node) for mother in node.mother_nodes)
        entry = entries.get(node.recipe)
        if entry is None:
            entries[node.recipe] = [node.recipe, node.machine, node.machine_nb, node.layer,
                                    node.needed_item, fed, inside, node, supplied_items(node)]
        else:
            entry[2] += node.machine_nb
            entry[3] = min(entry[3], node.layer)
            entry[5] += fed
            entry[6] = entry[6] or inside
            entry[8] += [item for item in supplied_items(node) if item not in entry[8]]
    return sorted(entries.values(), key=lambda entry: (entry[3], entry[0].display_name))

class Output_Node(Node):
    def __init__(self, item, rate, is_byproduct=False):
        super().__init__()
        self.item = item
        self.rate = rate
        self.is_byproduct = is_byproduct
        self.picture = item.picture
        self.ingredients = [{"item": item, "rate": rate, "from": {}}]

# what every machine of the tree draws, as one node they all take from. It
# asks nothing of anything: it is the sum of what is asked of it.
class Power_Node(Node):
    def __init__(self):
        super().__init__()
        self.item = POWER_ITEM
        self.rate = 0.0          # what everything draws: the machines under it, and the extra
        self.generated = 0.0     # what the generators over it make
        self.needed_rate = 0.0   # how much generation was asked for
        self.machine_rate = 0.0  # what the machines under it draw, alone
        self.extra = []          # what draws on it from outside the tree (see set_extra_draw)
        # what its augmenters add to the whole grid, as a share of that grid's
        # power (see refresh_power) - and that share in megawatts, once the
        # grid it is on says how much it makes (set by whoever knows the grid)
        self.boost_fraction = 0.0
        self.boost = 0.0
        self.picture = ""
        self.products = [{"item": POWER_ITEM, "rate": 0.0, "to": {}}]
        # asking for power is asking this node for it: the generators that
        # answer hang under it like any other supplier
        self.ingredients = [{"item": POWER_ITEM, "rate": 0.0, "from": {}}]

    def recalculate(self):
        self.machine_rate = sum(self.products[0]["to"].values())
        self.rate = self.products[0]["rate"] = self.machine_rate + sum(entry["power"] for entry in self.extra)
        self.ingredients[0]["rate"] = self.needed_rate
        self.generated = sum(self.ingredients[0]["from"].values())

    # what it makes with its augmenters' boost (see boost) - what it says it makes
    @property
    def made(self):
        return self.generated + self.boost

# A building that only draws power - a train station, a radar tower - asked
# for by the output panel's Consumer list: `count` of them, drawing what they
# draw on the power node, nothing going in or coming out. It stands on the
# map as a node of its own, its line running up to the power node.
class Consumer_Node(Node):
    def __init__(self, building, count):
        super().__init__()
        self.building = building
        self.count = count
        self.machine_nb = count          # how many stand, as a machine count is read
        self.needed_power = building.power * count
        self.picture = building.picture
        self.ingredients = [{"item": POWER_ITEM, "rate": self.needed_power, "from": {}}]
        self.products = []

    @property
    def item(self):
        return None

class Manual_Node(Node):
    def __init__(self, mother_nodes, item, needed_rate=0):
        super().__init__(mother_nodes)
        self.item = item
        self.needed_rate = needed_rate
        self.picture = item.picture
        self.recalculate()

    def recalculate(self):
        # what its takers ask for once there are any - on its creation, before
        # the first is written in, the rate it was made for
        asked = sum(sum(entry["to"].values()) for entry in self.products)
        self.rate = asked if any(entry["to"] for entry in self.products) else self.needed_rate
        self.products = [flow_entry(self.products, self.item, self.rate, "to")]

# Where an extraction box digs its item from, as the project map draws it:
# a box left of it, feeding it what it is asked for. It is no part of the
# tree - the map adds it on top (see with_sources in the interface) - so it
# is not linked into anything, only kept on its extraction.
class Source_Node(Node):
    def __init__(self, extraction):
        super().__init__()
        self.extraction = extraction
        self.item = extraction.needed_item
        self.picture = self.item.picture
        self.recalculate()

    def recalculate(self):
        self.rate = self.extraction.needed_rate
        self.products = [{"item": self.item, "rate": self.rate, "to": {self.extraction: self.rate}}]

class Recipe_Node(Node):
    # `recipe` is one of the item's own recipes to run; None takes the first,
    # the item's default
    def __init__(self, mother_nodes, needed_item, needed_rate, recipe=None):
        super().__init__(mother_nodes)
        self.needed_item = needed_item
        self.needed_rate = needed_rate
        self.possible_recipes = needed_item.recipes
        self.recipe = recipe if recipe in self.possible_recipes else self.possible_recipes[0]
        # a miner's extraction runs in the miner of the planner's mark, and
        # takes that miner's time; any other recipe its own machine and time
        durations = getattr(self.recipe, "miner_durations", None)
        if durations:
            self.machine = next((m for m in durations if m.full_name == MINER_NAME.format(MINER_MARK)),
                                self.recipe.machine[0])
            self.duration = durations[self.machine]
        else:
            self.machine = self.recipe.machine[0]
            self.duration = self.recipe.duration
        # the machine it runs in on no node of the hub's: an extraction stood
        # on nodes shows theirs instead (see stand_on_sites), and goes back to
        # this one once they are taken off it - or deleted
        self.own_machine = self.machine

        self.item_picture = needed_item.picture
        self.machine_picture = self.machine.picture

        #shown info
        self.recipe_name = self.recipe.display_name
        self.is_alternate = self.recipe.is_alternate
        self.recalculate()

        # recalculate builds the products with nobody down for them yet, so the
        # parents this node was born with are written in after it
        for mother in self.mother_nodes:
            self.deliver(needed_item, mother, needed_rate)

    # what this node delivers, the same question every producer answers
    @property
    def item(self):
        return self.needed_item

    # machines running this recipe to make `rate` of `item` a minute. One craft
    # yields amount every duration seconds, so amount / duration * 60 is what a
    # single machine delivers
    def machines_for(self, item, rate):
        product = next(p for p in self.recipe.products if p["item"] == item)
        return rate / (product["amount"] / self.duration * 60)

    # An extraction on assigned resource nodes: what it is asked for poured
    # into them in their order, each full before the next, one extractor on
    # every node it reaches - clocked to what it gives there. Whatever they
    # cannot give is left to the planner's own miners, counted as before.
    # The machine it shows is the one most of those nodes carry.
    def stand_on_sites(self):
        sites = EXTRACTION_SITES.get(self.needed_item) if not self.recipe.ingredients else None
        self.on_sites = bool(sites)   # its power then read off its clocks, not its count
        if not sites:
            return
        left, used, power = self.needed_rate, [], 0.0
        for machine, capacity, base in sites:
            if left <= 1e-9:
                break
            poured = min(left, capacity)
            if poured <= 0:
                continue
            left -= poured
            used.append(machine)
            draw = self.recipe.average_power or machine.power_consuption
            power += draw * (poured / base) ** Machine.POWER_EXPONENT if base else 0.0
        extra = self.machines_for(self.needed_item, left) if left > 1e-9 else 0.0
        if extra:
            power += power_for(self, extra)
        if used:
            self.machine = max(set(used), key=used.count)
            self.machine_picture = self.machine.picture
        self.machine_nb = len(used) + extra
        self.full_machines = int(self.machine_nb)
        self.last_machine_clock = self.machine_nb - self.full_machines
        self.machine_built = self.full_machines + (1 if self.last_machine_clock else 0)
        self.needed_power = power

    # what every product is asked for, read off the repartition on it
    # byproducts only take what is left over, they never ask for more
    # - and neither do the takers drawing only on its leftovers
    def demands(self):
        return {entry["item"]: sum(rate for taker, rate in entry["to"].items()
                                   if not is_byproduct(taker) and not is_surplus_taker(entry, taker))
                for entry in self.products}

    def recalculate(self):
        # one machine count has to cover every product asked of the recipe, so
        # it is set by whichever demand needs the most machines - the others
        # come out of the same crafts, over produced. Read before the lists are
        # rebuilt below, since it is those lists it reads.
        #
        # on its creation nobody is written in as taking anything yet, so an
        # empty repartition falls back to the rate it was made for. Takers
        # asking for nothing size it down to nothing.
        wanted = {item: rate for item, rate in self.demands().items() if rate > 0}
        if wanted:
            self.needed_item, self.needed_rate = max(
                wanted.items(), key=lambda demand: self.machines_for(*demand))
        elif any(entry["to"] for entry in self.products):
            self.needed_rate = 0
        self.machine_nb = self.machines_for(self.needed_item, self.needed_rate)

        crafts_per_minute = 60 / self.duration * self.machine_nb

        previous = self.ingredients   # kept: who supplies what has to survive
        self.ingredients = [flow_entry(previous, e["item"],
                                       e["amount"] * crafts_per_minute, "from")
                            for e in self.recipe.ingredients]
        self.products = [flow_entry(self.products, e["item"],
                                    e["amount"] * crafts_per_minute, "to")
                         for e in self.recipe.products]

        # 1.5 machines means two buildings: one at 100% and one underclocked to 50%.
        # Power is not linear with the clock, the underclocked one draws
        # power * 0.5 ** 1.321929, about 40% of full, not half.
        self.full_machines = int(self.machine_nb)
        self.last_machine_clock = self.machine_nb - self.full_machines
        self.machine_built = self.full_machines + (1 if self.last_machine_clock else 0)
        self.machine = self.own_machine
        self.machine_picture = self.machine.picture
        self.needed_power = power_for(self, self.machine_nb)
        self.stand_on_sites()

        # the power it draws is an ingredient like any other, so the graph can
        # carry a line from the power node into it (see refresh_power). It is
        # not one of the recipe's own, so it is written in after them.
        if self.needed_power > 0:
            self.ingredients.append(flow_entry(previous, POWER_ITEM, self.needed_power, "from"))


