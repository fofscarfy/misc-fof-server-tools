from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Tuple, Dict, Set
from math import dist
import json
import os
from random import choices, random, shuffle
from argparse import ArgumentParser

@dataclass
class FofPropObj:
    _id=0
    
    entity: str
    data: str
    origin: Tuple[float, float, float]
    direction: Tuple[float, float, float]
    id_: str = "-1"

    def __post_init__(self):
        if self.id_ == "-1":
            self.id_ = str(type(self)._id)
            type(self)._id += 1

    def distance(self, other: 'FofPropObj'):
        return dist(self.origin, other.origin)

class FofRemixer:
    def __init__(self):
        
        ## Config Variables
        # Distance for whiskey to be a neighbor
        self.whiskey_neighbor_dist = float(os.environ.get("WHISKEY_NEIGHBOR_DIST", 20.0))
        
        # Distance for chest to be a neighbor
        self.chest_neighbor_dist = float(os.environ.get("CHEST_NEIGHBOR_DIST", 0.0))
        
        # Distance for crates to be a cluster (You don't want this)
        self.crate_neighbor_dist = float(os.environ.get("CRATE_NEIGHBOR_DIST", 0.0))
        
        # Probability of including a neighbor
        self.neighbor_chance = float(os.environ.get("NEIGHBOR_CHANCE", 1.0))
        
        # Distance Bias: How much distance weighs into where things are placed 
        # (0 = no weight, 1 = proportional, 10000.0 (or high number) -> almost always picks furthest)
        self.distance_bias = float(os.environ.get("DISTANCE_BIAS", 1.0))
        
        # Amount of whiskey to put on the map - (0 < val < 1 = percentage, integer = number)
        self.num_whiskey = float(os.environ.get("WHISKEY_AMOUNT", 0.333))
        
        # Number of blue crates - (0 < val < 1 = percentage, integer = number)
        self.blue_crate_amt = float(os.environ.get("BLUE_CRATE_AMOUNT", 3))
        
        # Number of red crates - (0 < val < 1 = percentage, integer = number)
        self.red_crate_amt = float(os.environ.get("RED_CRATE_AMOUNT", 2))
        
        # Number of gold crates - (0 < val < 1 = percentage, integer = number)
        self.gold_crate_amt = float(os.environ.get("GOLD_CRATE_AMOUNT", 1))

    def import_ai_script(self, input_script):
        self.item_categories = {}
        props = {}
        
        with open(input_script, "r") as fp:
            for line in fp:
                line = line.strip()
                if line == '"preset"':
                    if props != {}:
                        obj = FofPropObj(props["entity"], props["data"], 
                                            (float(props["origin_x"]), float(props["origin_y"]), float(props["origin_z"])), 
                                            (float(props["dir_x"]), float(props["dir_y"]), float(props["dir_z"])))
                        
                        if obj.entity not in self.item_categories:
                            self.item_categories[obj.entity] = {}
                        self.item_categories[obj.entity][obj.id_] = obj
                        
                        props = {}

                fields = line.split()
                if len(fields) == 2:
                    props[fields[0][1:-1]] = fields[1][1:-1]
        
        self.input_script = input_script
        
        if props != {}:
            obj = FofPropObj(props["entity"], props["data"], 
                                (float(props["origin_x"]), float(props["origin_y"]), float(props["origin_z"])), 
                                (float(props["dir_x"]), float(props["dir_y"]), float(props["dir_z"])))
            
            if obj.entity not in self.item_categories:
                self.item_categories[obj.entity] = {}
            self.item_categories[obj.entity][obj.id_] = obj

    def create_randomized_locations(self):
        self.chosen_objs = {}
        
        for cat, objs in self.item_categories.items():
            if len(objs) == 0: continue

            count = 0
            if cat == "item_whiskey":
                count = int(round(self.num_whiskey * len(objs)) \
                        if 0.0 < self.num_whiskey < 1.0 \
                        else min(self.num_whiskey, len(objs)))
                neighbor_dist = self.whiskey_neighbor_dist
            elif cat == "fof_crate":
                bc = int(round(self.blue_crate_amt * len(objs)) \
                        if 0.0 < self.blue_crate_amt < 1.0 \
                        else min(self.blue_crate_amt, len(objs)))
                rc = int(round(self.red_crate_amt * len(objs)) \
                        if 0.0 < self.red_crate_amt < 1.0 \
                        else min(self.red_crate_amt, len(objs)))
                gc = int(round(self.gold_crate_amt * len(objs)) \
                        if 0.0 < self.gold_crate_amt < 1.0 \
                        else min(self.gold_crate_amt, len(objs)))
                count = min(bc + rc + gc, len(objs))
                neighbor_dist = self.chest_neighbor_dist
            
            if count == 0: continue

            self.chosen_objs[cat] = {}
            chosen_set = set()
            distances = {x: 0.0 for x in objs}
            
            chosen = 0
            
            
            while chosen < count:
                # Calculating weights for choices
                total = sum(distances.values())
                if chosen > 0:
                    probs = [x / total for x in distances.values()]
                    pmax = max(probs)
                    probs = [(x / pmax) ** self.distance_bias for x in probs]
                else:
                    probs = [1] * len(distances)
                
                # Making a choice
                choice = choices(list(distances.keys()), weights=probs, k=1)[0]
                chosen_set.add(choice)
                self.chosen_objs[cat][choice] = objs[choice]
                del distances[choice]
                
                chosen += 1
                
                # Doing neighbors/simple clustering
                queue = list(zip(distances.keys(), [choice] * len(distances)))
                
                while queue:
                    obj, parent = queue.pop(0)
                    if obj not in distances: continue

                    objdist = objs[obj].distance(objs[parent])
                    
                    if objdist > neighbor_dist:
                        if parent in chosen_set:
                            distances[obj] = objdist if distances[obj] == 0 else min(objdist, distances[obj])
                    else:
                        if random() < self.neighbor_chance:
                            chosen_set.add(obj)
                            self.chosen_objs[cat][obj] = objs[obj]
                            chosen += 1
                            del distances[obj]
                            if chosen == count:
                                break
                        queue += list(zip(distances.keys(), [obj] * len(distances)))
                            
            if cat == "fof_crate":
                chests = ["fof_crate"] * gc + ["fof_crate_med"] * rc + ["fof_crate_low"] * bc
                shuffle(chests)
                
                for idx, obj in enumerate(self.chosen_objs[cat].values()):
                    obj.entity = chests[idx]
                    
                    
    def export_to_script(self, ai_output):
        out_str = '"PropList"\n{\n'
        
        for objs in self.chosen_objs.values():
            for obj in objs.values():
                out_str += '\t"preset"\n\t{\n'
                out_str += f'\t\t"entity"\t\t"{obj.entity}"\n'
                out_str += f'\t\t"data"\t\t"{obj.data}"\n'
                out_str += f'\t\t"origin_x"\t\t"{obj.origin[0]:.6f}"\n'
                out_str += f'\t\t"origin_y"\t\t"{obj.origin[1]:.6f}"\n'
                out_str += f'\t\t"origin_z"\t\t"{obj.origin[2]:.6f}"\n'
                out_str += f'\t\t"dir_x"\t\t"{obj.direction[0]:.6f}"\n'
                out_str += f'\t\t"dir_y"\t\t"{obj.direction[1]:.6f}"\n'
                out_str += f'\t\t"dir_z"\t\t"{obj.direction[2]:.6f}"\n'
                out_str += '\t}\n'
                
        out_str += "}"
        
        with open(ai_output, "w") as fp:
            fp.write(out_str)     
            
if __name__ == "__main__":
    ENV_FILE = "configs/remixer.env"
    
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
    
    parser = ArgumentParser(description="Script for randomizing chest and whiskey placement on maps.")
    parser.add_argument('map_name', type=str, help='The map name of the map whose chests/whiskey to randomize')
    args = parser.parse_args()
    
    input_script = f"data/map_prop_templates/chest-whiskey-templates/{args.map_name}-shootout-template.ai"
    output_script = f"fof/fof_scripts/ai_editor/{args.map_name}-shootout.ai"
    
    if os.path.exists(input_script):
        remixer = FofRemixer()
        remixer.import_ai_script(input_script)
        remixer.create_randomized_locations()
        remixer.export_to_script(output_script)
    else:
        print(f"File {input_script} does not exist!")
