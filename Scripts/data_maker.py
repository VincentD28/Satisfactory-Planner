# Author      : Vincent Dufresne
# Date        : 12-08-2026
# Description : Take the raw json file and create a new one 
#               that will be easier to process in the tree creator script


import hashlib
import json
import os
import re
import sys

# The game's own docs, written out beside the install: the source this whole
# file is built from. Read where Steam puts it rather than from a copy kept
# here, so a game update is picked up by running this again. A copy sitting
# next to this script is used instead when there is one - a machine without
# the game installed, say.
GAME_DOCS = r"C:\Program Files (x86)\Steam\steamapps\common\Satisfactory\CommunityResources\Docs\en-CA.json"

# The planner keeps itself in three folders beside one another: Scripts (this
# file and its two neighbours), Images (every picture the graph draws) and
# Data (what the planner reads and writes - the cleaned game data, what it was
# made from, and the projects). Everything here answers where those are.
#
# Built into an exe it is the same three folders, beside the exe rather than
# beside the scripts: PyInstaller unpacks the code into a temporary folder of
# its own (sys._MEIPASS, gone the moment the app closes), so nothing the
# planner writes can live there.
FROZEN = getattr(sys, "frozen", False)
SCRIPTS = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(sys.executable) if FROZEN else os.path.dirname(SCRIPTS)
IMAGES = os.path.join(ROOT, "Images")
DATA = os.path.join(ROOT, "Data")

# a file the planner writes: in Data, which is made if it is not there yet
def kept_file(name):
    try:
        os.makedirs(DATA, exist_ok=True)
    except OSError:
        pass
    return os.path.join(DATA, os.path.basename(name))

# A file it only reads, by the name the data knows it as. A picture is named
# for where it used to sit ("img/Desc_Rotor_C.png") and is looked for in
# Images; everything else is one of the planner's own files, in Data. A copy
# carried inside the exe stands in for one that is not there.
def data_file(name):
    plain = os.path.basename(name)
    home = IMAGES if name.replace("\\", "/").startswith("img/") else DATA
    whole = os.path.join(home, plain)
    if os.path.exists(whole):
        return whole
    carried = os.path.join(SCRIPTS, name.replace("\\", "/"))
    return carried if os.path.exists(carried) else whole

LOCAL_DOCS = os.path.join(DATA, "en-CA.json")

# What the cleaned data was last built from, kept beside it: the file itself
# and a fingerprint of its contents, so the app can tell whether the game has
# been updated since (see Interface, the home page).
SOURCE_RECORD = kept_file("data_source.json")

def fingerprint(path):
    digest = hashlib.sha1()
    with open(path, "rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()

# What version of the game a docs file belongs to. Unreal writes it beside
# the executable, a few folders up from the docs:
#   <install>/Engine/Binaries/Win64/FactoryGame*-Shipping.version
# which holds "GameVersion" ("1.2.4.0") and the build it was made from. The
# file name differs between the Steam and Epic builds, so any .version there
# is taken.
def game_version(docs_path):
    root = os.path.dirname(os.path.dirname(os.path.dirname(docs_path or "")))
    binaries = os.path.join(root, "Engine", "Binaries", "Win64")
    try:
        names = [n for n in os.listdir(binaries) if n.lower().endswith(".version")]
    except OSError:
        return {}
    for name in names:
        try:
            with open(os.path.join(binaries, name), encoding="utf-8") as file:
                said = json.load(file)
        except Exception:
            continue
        if said.get("GameVersion"):
            return {"version": said["GameVersion"], "build": str(said.get("BuildId") or "")}
    return {}

def source_record():
    try:
        with open(SOURCE_RECORD, encoding="utf-8") as file:
            return json.load(file) or {}
    except Exception:
        return {}

# The version noted against data that was made before versions were noted -
# only ever called when the file still matches what the data was built from,
# so it is filling in what was known all along rather than guessing.
def remember_version(docs_path):
    record = source_record()
    found = game_version(docs_path)
    if not found.get("version") or record.get("version") == found["version"]:
        return record
    record.update(found)
    try:
        with open(SOURCE_RECORD, "w", encoding="utf-8") as file:
            json.dump(record, file, indent=1)
    except OSError:
        pass
    return record

def original_data_path():
    if os.path.exists(LOCAL_DOCS):
        return LOCAL_DOCS
    if os.path.exists(GAME_DOCS):
        return GAME_DOCS
    raise FileNotFoundError("en-CA.json not found - looked beside this script and at " + GAME_DOCS)

# icon files live in img/, named after the game's own texture asset (see extract_icons.py)
ICON_ASSET_RE = re.compile(r"/Game/.+/(\w+)\.")

def parse_icon(entry):
    raw = entry.get("mSmallIcon") or entry.get("mPersistentBigIcon") or ""
    match = ICON_ASSET_RE.search(raw)
    return f"img/{match.group(1)}.png" if match else ""

# The entries of one block of en-CA.json, found by the class name at the end
# of its NativeClass field rather than by where it sits in the file. The game
# writes the blocks in whatever order it likes: 1.2.4.0 swapped the first two
# (items and resources) around, and reading them by position turned every
# solid item into something a miner could dig up.
BLOCK_CLASS = re.compile(r"FactoryGame\.(\w+)'")

def blocks_by_name(data):
    found = {}
    for block in data:
        name = BLOCK_CLASS.search(block.get("NativeClass", ""))
        if name:
            found.setdefault(name.group(1), []).extend(block["Classes"])
    return found

# What the file held when this was written, for reference: the order it was
# in, and how many entries each block had. Nothing reads it any more.
BLOCK = {
    "FGItemDescriptor":                        0,  # 122
    "FGResourceDescriptor":                    1,  # 13
    "FGBuildableWallLightweight":              2,  # 73
    "FGRecipe":                                3,  # 872
    "FGConsumableEquipment":                   4,  # 2
    "FGEquipmentStunSpear":                    5,  # 3
    "FGEquipmentDescriptor":                   6,  # 17
    "FGCustomizationRecipe":                   7,  # 106
    "FGObjectScanner":                         8,  # 1
    "FGItemDescriptorBiomass":                 9,  # 16
    "FGConsumableDescriptor":                 10,  # 5
    "FGBuildable":                            11,  # 16
    "FGBuildingDescriptor":                   12,  # 547
    "FGVehiclePathSegment":                   13,  # 5
    "FGAmmoTypeProjectile":                   14,  # 13
    "FGBuildableRailroadTrack":               15,  # 1
    "FGBuildableBeam":                        16,  # 8
    "FGWeapon":                               17,  # 2
    "FGAmmoTypeSpreadshot":                   18,  # 1
    "FGAmmoTypeInstantHit":                   19,  # 2
    "FGGasMask":                              20,  # 1
    "FGSuitBase":                             21,  # 1
    "FGJetPack":                              22,  # 1
    "FGChargedWeapon":                        23,  # 1
    "FGBuildableTradingPost":                 24,  # 1
    "FGBuildablePoleConveyor":                25,  # 1
    "FGBuildablePoleBase":                    26,  # 1
    "FGBuildableConveyorBelt":                27,  # 6
    "FGBuildablePowerPole":                   28,  # 11
    "FGBuildableWire":                        29,  # 2
    "FGSchematic":                            30,  # 574
    "FGBuildableStair":                       31,  # 2
    "FGBuildableWalkwayLightweight":          32,  # 10
    "FGBuildableWalkway":                     33,  # 1
    "FGBuildableWall":                        34,  # 3
    "FGBuildablePillarLightweight":           35,  # 9
    "FGBuildableFactory":                     36,  # 3
    "FGBuildableGeneratorFuel":               37,  # 3
    "FGBuildableStorage":                     38,  # 5
    "FGBuildableResourceExtractor":           39,  # 4
    "FGPortableMinerDispenser":               40,  # 1
    "FGBuildableManufacturer":                41,  # 8
    "FGBuildableSpaceElevator":               42,  # 1
    "FGBuildableCornerWall":                  43,  # 12
    "FGBuildableDoor":                        44,  # 10
    "FGBuildableFoundationLightweight":       45,  # 153
    "FGBuildableRampLightweight":             46,  # 78
    "FGBuildableLadder":                      47,  # 1
    "FGBuildablePipeReservoir":               48,  # 2
    "FGBuildablePipelinePump":                49,  # 3
    "FGBuildablePoleStackable":               50,  # 3
    "FGBuildablePolePipe":                    51,  # 2
    "FGBuildablePassthrough":                 52,  # 2
    "FGPipeHyperStart":                       53,  # 1
    "FGBuildablePipeHyperJunction":           54,  # 2
    "FGBuildablePipeHyper":                   55,  # 1
    "FGBuildablePipelineJunction":            56,  # 2
    "FGBuildableWaterPump":                   57,  # 1
    "FGBuildableResourceSink":                58,  # 1
    "FGBuildableResourceSinkShop":            59,  # 1
    "FGBuildablePipeline":                    60,  # 4
    "FGItemDescriptorNuclearFuel":            61,  # 3
    "FGBuildableDroneStation":                62,  # 1
    "FGGolfCartDispenser":                    63,  # 2
    "FGVehicleDescriptor":                    64,  # 8
    "FGBuildableLightSource":                 65,  # 2
    "FGBuildableFloodlight":                  66,  # 2
    "FGBuildableStackableShelf":              67,  # 1
    "FGBuildableCornerWallLightweight":       68,  # 24
    "FGBuildableElevatorFloorStop":           69,  # 1
    "FGBuildableElevator":                    70,  # 1
    "FGBuildableLightsControlPanel":          71,  # 1
    "FGBuildableWidgetSign":                  72,  # 10
    "FGBuildablePassthroughPipeHyper":        73,  # 1
    "FGBuildableBarrierCorner":               74,  # 1
    "FGBuildableConveyorMonitor":             75,  # 1
    "FGBuildableFactoryBuilding":             76,  # 3
    "FGBuildableManufacturerVariablePower":   77,  # 3
    "FGBuildableConveyorLift":                78,  # 6
    "FGPowerShardDescriptor":                 79,  # 2
    "FGBuildableFrackingExtractor":           80,  # 1
    "FGBuildableFrackingActivator":           81,  # 1
    "FGBuildableGeneratorNuclear":            82,  # 1
    "FGChainsaw":                             83,  # 1
    "FGBuildableSnowDispenser":               84,  # 1
    "FGBuildableSnowCannon":                  85,  # 1
    "FGBuildableFactorySimpleProducer":       86,  # 1
    "FGBuildableMergerPriority":              87,  # 1
    "FGBuildableRadarTower":                  88,  # 1
    "FGParachute":                            89,  # 1
    "FGBuildableGeneratorGeoThermal":         90,  # 1
    "FGBuildableSplitterSmart":               91,  # 2
    "FGBuildablePriorityPowerSwitch":         92,  # 1
    "FGJumpingStilts":                        93,  # 1
    "FGBuildableCircuitSwitch":               94,  # 1
    "FGEquipmentZipline":                     95,  # 1
    "FGBuildablePowerBooster":                96,  # 1
    "FGCentralStorageContainer":              97,  # 1
    "FGItemDescriptorPowerBoosterFuel":       98,  # 1
    "FGBuildablePortal":                      99,  # 1
    "FGBuildablePortalSatellite":            100,  # 1
    "FGBuildableBlueprintDesigner":          101,  # 3
    "FGHoverPack":                           102,  # 1
    "FGBuildableRailroadSignal":             103,  # 2
    "FGBuildableRailroadAttachment":         104,  # 1
    "FGBuildableRailroadStation":            105,  # 1
    "FGBuildableTrainPlatformCargo":         106,  # 2
    "FGBuildableTrainPlatformEmpty":         107,  # 2
    "FGBuildableDockingStation":             108,  # 2
    "FGBuildablePowerStorage":               109,  # 1
    "FGBuildableJumppad":                    110,  # 1
    "FGBuildableMAM":                        111,  # 1
    "FGBuildableAttachmentMerger":           112,  # 1
    "FGBuildableAttachmentSplitter":         113,  # 1
}

LITERS_PER_M3 = 1000   # what a fluid's amounts are divided by as the data is cleaned

MANUAL_PRODUCERS = {
    "BP_BuildGun_C", "FGBuildGun",
    "BP_WorkBenchComponent_C", "BP_WorkshopComponent_C",
    "FGBuildableAutomatedWorkBench", "Build_AutomatedWorkBench_C",
}

class Item:
    # id is the order the item was first met while reading the game data, which
    # is also the order it sits in the json - the game lists its items roughly
    # by progression, so it reads far better in a menu than an alphabetical sort
    # form is the game's mForm: RF_SOLID for anything on a belt, RF_LIQUID or
    # RF_GAS for anything in a pipe. A fluid's amounts are in cubic meters,
    # not items - the game's own liters, divided down as the data is cleaned.
    # Defaults to solid so a cleaned_data.json written before it existed still loads.
    def __init__(self, id, full_name, display_name, recipes, picture="", form="RF_SOLID"):
        self.id = id
        self.full_name = full_name
        self.display_name = display_name
        self.recipes = recipes
        self.picture = picture      # path to the icon, empty until one is set
        self.form = form

    @property
    def is_fluid(self):
        return self.form in ("RF_LIQUID", "RF_GAS")

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "recipes": self.recipes,
            "picture": self.picture,
            "form": self.form,
        }

class Recipe:
    # power_min/power_max: a few recipes are not run at their machine's own
    # draw but over a range of it - the particle accelerator, the converter and
    # the quantum encoder swing between the two while they craft, and their
    # machines carry no draw of their own at all. Both 0 for every other
    # recipe, which draws what its machine draws.
    def __init__(self, full_name, display_name, products, ingredients, duration, machine,
                 is_alternate, power_min=0.0, power_max=0.0):
        self.full_name = full_name
        self.display_name = display_name
        self.products = products
        self.ingredients = ingredients
        self.duration = duration
        self.machine = machine
        self.is_alternate = is_alternate
        self.power_min = power_min
        self.power_max = power_max

    # what one machine running it draws on average, or 0 when it just draws
    # whatever its machine does
    @property
    def average_power(self):
        return (self.power_min + self.power_max) / 2 if self.power_max else 0.0

    def to_dict(self):
        return {
            "full_name": self.full_name,
            "display_name": self.display_name,
            "products": self.products,
            "ingredients": self.ingredients,
            "duration": self.duration,
            "machine": self.machine,
            "is_alternate": self.is_alternate,
            "power_min": self.power_min,
            "power_max": self.power_max,
        }

class Machine:
    # Same on every overclockable building in the game data, so they live here
    # instead of being carried per machine through the json.
    # power draw = power_consuption * clock ** POWER_EXPONENT
    #              and again * boost ** BOOST_POWER_EXPONENT with somersloops
    POWER_EXPONENT = 1.321929        # log2(2.5) : double the clock, 2.5x the power
    BOOST_POWER_EXPONENT = 2.0       # double the output, 4x the power

    def __init__(self, full_name, display_name, ingredients, power_consuption,
                 #min_variable_power=None, max_variable_power=None, 
                 sloop_slots=0, picture="",
                 extract_cycle_time=None, items_per_cycle=None, allowed_resources=None):
        self.full_name = full_name
        self.display_name = display_name
        self.ingredients = ingredients
        self.power_consuption = power_consuption
        self.picture = picture      # path to the icon, empty until one is set
        # self.min_variable_power = min_variable_power   
        # self.max_variable_power = max_variable_power         
        self.sloop_slots = sloop_slots

        # - used for exctraction recipe creation -                
        self.extract_cycle_time = extract_cycle_time  
        self.items_per_cycle = items_per_cycle        
        self.allowed_resources = allowed_resources    

    def to_dict(self):
        return {
            "full_name": self.full_name,
            "display_name": self.display_name,
            "ingredients": self.ingredients,
            "power_consuption": self.power_consuption,
            # "min_variable_power": self.min_variable_power,
            # "max_variable_power": self.max_variable_power,
            "sloop_slots": self.sloop_slots,
            "picture": self.picture,
            "extract_cycle_time": self.extract_cycle_time,
            "items_per_cycle": self.items_per_cycle,
            "allowed_resources": self.allowed_resources,
        }
        

# Separate and return the O/I part of the json field
OI_FORM = re.compile(r"\.(\w+_C)'\",Amount=([\d.]+)")
def parse_item_list(raw):
    return [
        {
            "item": name, # temporary, will be the item ref after being extracted from the json
            "amount": float(amount)
        }
        for name, amount in OI_FORM.findall(raw)
    ]

# Separate and return the allowed ressource part of the json field
RESOURCE_FORM = re.compile(r"\.(\w+_C)'")
def parse_resource_list(raw):
    return RESOURCE_FORM.findall(raw)

# Every producer listed in mProducedIn: real machines (Build_*_C), the workbench
# and workshop components, and the native FGBuildable* classes.
RECIPE_MACHINE_FORM = re.compile(r"\.(\w+)\"")
def parse_machine_list(raw):
    return RECIPE_MACHINE_FORM.findall(raw)


def clean_data(source=None):
    # uses "ClassName" for key
    All_Items = {}
    All_Recipes = {}
    All_Machines = {}
    All_data_entries = {}

    # === ORIGINAL_DATA --> All_Items and All_Recipes ===

    SOURCE_PATH_ORIGINAL_DATA = source or original_data_path()
    print(f"reading {SOURCE_PATH_ORIGINAL_DATA}")
    with open(SOURCE_PATH_ORIGINAL_DATA, encoding="utf-16") as s:
        data = json.load(s)

        blocks = blocks_by_name(data)
        for block in data:
            for e in block["Classes"]:
                All_data_entries[e["ClassName"]] = e

        def get_item(full_name):
            if full_name not in All_Items:
                entry = All_data_entries[full_name]
                All_Items[full_name] = Item(
                    id=len(All_Items),   # first one in gets 0, and so on down the file
                    full_name=full_name, display_name=entry["mDisplayName"], recipes=[],
                    picture=parse_icon(entry),
                    form=entry.get("mForm", "RF_SOLID"),
                )
            return All_Items[full_name]
        
        # -- Recipes instanciation --

        # the game writes a constant of 0 and a factor of 1 on every recipe
        # that has no range at all, so those are read as "no range"
        def power_range(r):
            constant = float(r.get("mVariablePowerConsumptionConstant", 0) or 0)
            factor = float(r.get("mVariablePowerConsumptionFactor", 1) or 1)
            if constant == 0 and factor == 1:
                return 0.0, 0.0
            return constant, constant + factor

        for r in blocks["FGRecipe"]:
            non_manual_machines = set(parse_machine_list(r["mProducedIn"])) - MANUAL_PRODUCERS
            if not non_manual_machines:  # hand-crafted only
                continue
            low, high = power_range(r)
            All_Recipes[r["ClassName"]] = Recipe(
                full_name=r["ClassName"],
                display_name=r["mDisplayName"],
                products=parse_item_list(r["mProduct"]),
                ingredients=parse_item_list(r["mIngredients"]),
                duration=float(r["mManufactoringDuration"]),
                machine=sorted(non_manual_machines),
                is_alternate=r["ClassName"].startswith("Recipe_Alternate"),
                power_min=low,
                power_max=high,
            )
            # add to All_items
            for product_item in parse_item_list(r["mProduct"]):
                get_item(product_item["item"]).recipes.append(r["ClassName"])

            # no recipe added
            for ingredient_item in parse_item_list(r["mIngredients"]):
                get_item(ingredient_item["item"])
                
        print(f"All_Recipes: {len(All_Recipes)} recipes instanciated.")


        # -- Machines instanciation --
        
        MACHINE_BLOCKS = (
            "FGBuildableManufacturer",              # 8  fixed power
            "FGBuildableManufacturerVariablePower", # 3  particle acc, converter, quantum encoder
            "FGBuildableResourceExtractor",         # 4  miners Mk1-3, oil extractor
            "FGBuildableWaterPump",                 # 1  water extractor
            "FGBuildableFrackingExtractor",         # 1  resource well extractor
            "FGBuildableFrackingActivator",         # 1  resource well pressurizer
            "FGBuildableGeneratorFuel",             # 3  biomass burner, coal and fuel generators
            "FGBuildableGeneratorNuclear",          # 1  nuclear power plant
            "FGBuildableGeneratorGeoThermal",       # 1  geothermal generator
        )

        for b in MACHINE_BLOCKS:
            for m in blocks.get(b, ()):
                # the buildable itself carries no icon; its FGBuildingDescriptor
                # counterpart (the build-menu entry) does
                descriptor = All_data_entries.get("Desc_" + m["ClassName"].removeprefix("Build_"), {})
                All_Machines[m["ClassName"]] = Machine(
                    full_name = m["ClassName"],
                    display_name = m["mDisplayName"],
                    ingredients = parse_item_list(next(e["mIngredients"] for e in blocks["FGRecipe"] if "Desc_" + m["ClassName"].removeprefix("Build_") + "'" in e["mProduct"])),
                    power_consuption = float(m["mPowerConsumption"]),
                    picture = parse_icon(descriptor),
                    # min_variable_power = None   
                    # max_variable_power = None         
                    sloop_slots = (0 if m["mCanChangeProductionBoost"] != "True"
                                   else int(m["mProductionShardSlotSize"]) if m["mOverrideProductionShardSlotSize"] == "True"
                                   else 1),
                    extract_cycle_time = float(m["mExtractCycleTime"]) if "mExtractCycleTime" in m else None,
                    items_per_cycle = int(m["mItemsPerCycle"]) if "mItemsPerCycle" in m else None,
                    allowed_resources = parse_resource_list(m.get("mAllowedResources", "")),  
                )
        print(f"All_Machines: {len(All_Machines)} machines instanciated.")
        
        # -- Extraction recipes instanciation --

        SOLID_RESOURCES = [r["ClassName"] for r in blocks["FGResourceDescriptor"]
                                   if r["mForm"] == "RF_SOLID"]
        extraction_receipe_count = 0
        for machine_name, m in All_Machines.items():
            if m.extract_cycle_time is None:  # not an extractor
                continue
            for resource in (m.allowed_resources or SOLID_RESOURCES):  # empty means any solid
                recipe_name = f"Extract_{resource}_{machine_name}"
                All_Recipes[recipe_name] = Recipe(
                    full_name=recipe_name,
                    # matches every other recipe's convention: just the
                    # product's own name, not the raw class name or machine
                    display_name=All_data_entries[resource]["mDisplayName"],
                    products=[{
                        "item": resource, # temporary, will be the item ref after being extracted from the json
                        "amount": float(m.items_per_cycle)
                    }],
                    ingredients=[],
                    duration=m.extract_cycle_time,
                    machine=[machine_name],
                    is_alternate=False,
                )
                extraction_receipe_count += 1
                # add to All_items
                get_item(resource).recipes.append(recipe_name)
                                
        print(f"All_Recipes addition: {extraction_receipe_count} extraction recipes instanciated.")

        # -- Power generation recipes instanciation --
        #
        # A generator burns a fuel and makes power, which is nothing but a
        # recipe read the other way round: the fuel (and the water a coal or
        # nuclear plant drinks) go in, megawatts come out, along with whatever
        # the fuel leaves behind - a nuclear plant's waste.
        #
        # Power is not an item the game ships, so one is made up to carry it.
        # A craft is one minute of running flat out, which is what makes the
        # numbers read straight off the recipe: the amounts are per minute, and
        # the power amount is simply what the generator produces.
        #
        #   fuel a minute = power / the fuel's energy value * 60
        #   water a minute = its ratio to power * power * 60
        #   waste a minute = fuel a minute * what one unit leaves
        #
        # Fluids are still in liters here; the pass further down turns them
        # into cubic meters with every other fluid amount.
        POWER_ITEM = "Desc_Power_C"
        All_Items[POWER_ITEM] = Item(
            id=len(All_Items), full_name=POWER_ITEM, display_name="Power", recipes=[],
            picture="",   # the map draws it a bolt of its own
        )
        GENERATION_MINUTE = 60.0

        power_recipe_count = 0
        for machine_name, m in All_Machines.items():
            entry = All_data_entries[machine_name]
            production = float(entry.get("mPowerProduction", 0) or 0)
            # the geothermal generator has no fixed output: it swings over a
            # range like the variable power machines, so it is taken at its
            # average, and it burns nothing at all
            if not production:
                low = float(entry.get("mVariablePowerProductionConstant", 0) or 0)
                high = low + float(entry.get("mVariablePowerProductionFactor", 0) or 0)
                production = (low + high) / 2
            if not production:
                continue

            water_ratio = float(entry.get("mSupplementalToPowerRatio", 0) or 0)
            burns = entry.get("mFuel") or [{"mFuelClass": "", "mSupplementalResourceClass": "",
                                            "mByproduct": "", "mByproductAmount": ""}]
            for fuel in burns:
                fuel_class = fuel.get("mFuelClass") or ""
                ingredients = []
                if fuel_class:
                    energy = float(All_data_entries.get(fuel_class, {}).get("mEnergyValue", 0) or 0)
                    if not energy:
                        continue   # nothing says how long a unit of it lasts
                    burn_rate = production / energy * GENERATION_MINUTE
                    ingredients.append({"item": fuel_class, "amount": burn_rate})
                    name = f"Burn {All_data_entries[fuel_class]['mDisplayName']}"
                else:
                    burn_rate = 0.0
                    name = All_data_entries[machine_name]["mDisplayName"]

                water = fuel.get("mSupplementalResourceClass") or ""
                if water and water_ratio:
                    ingredients.append({"item": water,
                                        "amount": water_ratio * production * GENERATION_MINUTE})

                products = [{"item": POWER_ITEM, "amount": production}]
                waste = fuel.get("mByproduct") or ""
                if waste and fuel.get("mByproductAmount"):
                    products.append({"item": waste,
                                     "amount": burn_rate * float(fuel["mByproductAmount"])})

                recipe_name = f"Generate_{fuel_class or machine_name}_{machine_name}"
                All_Recipes[recipe_name] = Recipe(
                    full_name=recipe_name,
                    display_name=name,
                    products=products,
                    ingredients=ingredients,
                    duration=GENERATION_MINUTE,
                    machine=[machine_name],
                    is_alternate=False,
                )
                power_recipe_count += 1
                for product in products:
                    get_item(product["item"]).recipes.append(recipe_name)
                for ingredient in ingredients:
                    get_item(ingredient["item"])

        print(f"All_Recipes addition: {power_recipe_count} power generation recipes instanciated.")

        # -- Items instanciation --
        # Already done in previous section
        print(f"All_Items: {len(All_Items)} items instanciated.")
            

        # # json class display
        # for c in data:
        #     print(c["NativeClass"].removeprefix("/Script/CoreUObject.Class'/Script/FactoryGame."))

        # # Machine display
        # for r in data[3]["Classes"]:
        #     print(r["mDisplayName"] + " --> " + ", ".join(m.strip("()\"").split("/")[-1].split(".")[-1] for m in r["mProducedIn"].split(",")))


    # === All_... --> CLEANED_DATA json ===

    # -- Recipe display priority --

        # Order each item's recipes the way the user should see them, the first
        # being what the planner makes it with unless told otherwise. Three
        # things decide it, in this order:
        #
        #   - a recipe that eats the item as well as making it can never stand
        #     on its own. Sulfuric acid's first recipe was Encased Uranium
        #     Cell, which makes acid on the side while drinking four times as
        #     much of it: asked for 20/min the planner climbed to hundreds of
        #     billions of refineries and never settled. Last, always.
        #   - a recipe that makes the item only on the side comes after the
        #     ones it is the point of. Compacted coal came from the Rocket
        #     Fuel recipe, which needs turbofuel, which needs compacted coal.
        #   - then the kind: 0 extraction, 1 normal, 2 converter, 3 alternate,
        #     4 unpackaging. Unpackaging is last because it makes nothing: it
        #     hands back what was packaged. It was the default for four items -
        #     empty canisters from unpackaging alumina, empty tanks from
        #     unpackaging nitric acid, and rocket fuel and turbofuel by
        #     unpackaging themselves.
        def recipe_kind(recipe_name):
            recipe = All_Recipes[recipe_name]
            if recipe_name.startswith("Extract_"):
                return 0
            if recipe_name.startswith("Recipe_Unpackage"):
                return 4
            if "Build_Converter_C" in recipe.machine:
                return 2
            if recipe.is_alternate:
                return 3
            return 1

        def recipe_priority(recipe_name, item_name):
            recipe = All_Recipes[recipe_name]
            eats_it = any(entry["item"] == item_name for entry in recipe.ingredients)
            on_the_side = recipe.products[0]["item"] != item_name
            return (eats_it, on_the_side, recipe_kind(recipe_name))

        for item in All_Items.values():
            item.recipes.sort(key=lambda name, item_name=item.full_name: recipe_priority(name, item_name))

    # -- Fluids from liters to cubic meters --

    # the game counts anything in a pipe by the liter, a thousand of them to
    # one of the cubic meters it shows the player. Every amount of a fluid is
    # divided here, once, so everything downstream - rates, pipe throughput,
    # what the planner prints - is in cubic meters and nothing has to convert.
    for recipe in All_Recipes.values():
        for entry in recipe.products + recipe.ingredients:
            if All_Items[entry["item"]].is_fluid:
                entry["amount"] /= LITERS_PER_M3
    for machine in All_Machines.values():
        for entry in machine.ingredients:
            if All_Items[entry["item"]].is_fluid:
                entry["amount"] /= LITERS_PER_M3


    output = {
        "items": {name: item.to_dict() for name, item in All_Items.items()},
        "recipes": {name: recipe.to_dict() for name, recipe in All_Recipes.items()},
        "machines": {name: machine.to_dict() for name, machine in All_Machines.items()},
    }

    with open(kept_file("cleaned_data.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    # ...and what it was made from, for the app to check against
    with open(SOURCE_RECORD, "w", encoding="utf-8") as f:
        json.dump({"path": SOURCE_PATH_ORIGINAL_DATA,
                   "fingerprint": fingerprint(SOURCE_PATH_ORIGINAL_DATA),
                   **game_version(SOURCE_PATH_ORIGINAL_DATA)}, f, indent=1)
    return SOURCE_PATH_ORIGINAL_DATA


if __name__ == "__main__":
    clean_data()
