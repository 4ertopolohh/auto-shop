"""Original, unbranded Elantra-inspired sedan. Run with Blender 5.2 Python/bpy.

Creates an editable .blend, an optimized GLB with named explosion layers,
QA reports and actual renders. No external model, logo or CAD is included.
"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'frontend/public/models'
SOURCE = ROOT / 'assets/3d'
REVIEW = ROOT / 'backend/.local/car-review'
for directory in (OUT, SOURCE, REVIEW): directory.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1

def material(name, rgb, roughness=.35, metallic=0, coat=0, emission=0):
    mat = bpy.data.materials.new('M_' + name)
    mat.use_nodes = True
    mat.diffuse_color = (*rgb, 1)
    bsdf = next(node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    for key, value in [('Base Color', (*rgb,1)), ('Metallic',metallic), ('Roughness',roughness), ('Coat Weight',coat), ('Coat Roughness',.14)]:
        bsdf.inputs[key].default_value=value
    if emission:
        bsdf.inputs['Emission Color'].default_value=(*rgb,1)
        bsdf.inputs['Emission Strength'].default_value=emission
    return mat

paint=material('Obsidian_Paint',(.006,.008,.011),.29,0,.55)
glass=material('Smoked_Glass',(.023,.040,.049),.12,.0,1)
rubber=material('Tire_Rubber',(.018,.020,.022),.82)
plastic=material('Graphite_Polymer',(.035,.041,.046),.55)
alloy=material('Brushed_Alloy',(.55,.58,.62),.27,1)
steel=material('Mechanical_Steel',(.23,.26,.28),.42,1)
leather=material('Interior_Charcoal',(.032,.035,.038),.72)
red=material('Brake_Caliper',(.25,.035,.022),.33,0,.4)
headlight=material('LED_Ice',(.80,.89,1),.18,.0,.5,2)
taillight=material('LED_Red',(.65,.015,.008),.2,.0,.5,1.8)

layers={}
def layer(name, offset, category=''):
    obj=bpy.data.objects.new(name,None)
    scene.collection.objects.link(obj)
    obj['explode']=list(offset)
    obj['category']=category
    layers[name]=obj
    return obj

chassis=layer('Layer_Chassis',(0,0,-.12),'suspension')
body=layer('Layer_Body',(0,0,.76),'engine')
canopy=layer('Layer_Canopy',(0,0,1.55),'filters')
interior=layer('Layer_Interior',(-.12,0,.36),'filters')
power=layer('Layer_Powertrain',(.55,0,.30),'engine')
power.location.z=-.16

def finish(obj,name,mat,parent,bevel=0,smooth=True):
    obj.name=name
    obj.parent=parent
    obj.data.materials.clear();obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.select_set(False)
    if bevel:
        mod=obj.modifiers.new('Precision_Edge','BEVEL');mod.width=bevel;mod.segments=3
        mod.limit_method='ANGLE';mod.harden_normals=True
    for polygon in obj.data.polygons:polygon.use_smooth=smooth
    if bevel:
        mod=obj.modifiers.new('Surface_Normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=50
    return obj

def box(name,loc,size,mat,parent,bevel=.025,rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object;obj.dimensions=size
    if rotation:obj.rotation_euler=rotation
    return finish(obj,name,mat,parent,bevel)

def mesh(name,verts,faces,mat,parent,bevel=0,solidify=0):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj)
    finish(obj,name,mat,parent,bevel)
    if solidify:
        mod=obj.modifiers.new('Panel_Thickness','SOLIDIFY');mod.thickness=solidify
    return obj

def cylinder(name,loc,radius,depth,mat,parent,axis='Z',vertices=40,bevel=.004):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    obj=bpy.context.object
    obj.rotation_euler = (math.pi/2,0,0) if axis=='Y' else (0,math.pi/2,0) if axis=='X' else (0,0,0)
    return finish(obj,name,mat,parent,bevel)

def tube(name,points,radius,mat,parent,segments=8):
    # Mesh tube, so export never depends on curve resolution or unsupported nodes.
    verts=[]
    for i,point in enumerate(points):
        center=Vector(point)
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        tangent.normalize();normal=tangent.cross(Vector((0,0,1)))
        if normal.length<.01:normal=tangent.cross(Vector((0,1,0)))
        normal.normalize();other=tangent.cross(normal).normalized()
        verts.extend(tuple(center+radius*(math.cos(j*2*math.pi/segments)*normal+math.sin(j*2*math.pi/segments)*other)) for j in range(segments))
    faces=[]
    for i in range(len(points)-1):
        for j in range(segments):
            a=i*segments+j;b=i*segments+(j+1)%segments;faces.append((a,b,b+segments,a+segments))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple((len(points)-1)*segments+j for j in range(segments)))
    return mesh(name,verts,faces,mat,parent)

def boolean(obj,cutter):
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Panel_Cut','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)

# Primary shell follows the low hood / long wheelbase / angular fastback silhouette.
stations=[(-2.35,.72,.83),(-2.24,.84,.91),(-1.94,.895,.98),(-1.46,.913,1.005),(-.8,.91,1.015),(.1,.908,1.02),(.72,.9,1.015),(1.35,.912,.95),(1.98,.87,.86),(2.28,.81,.80),(2.35,.75,.75)]
verts=[]
for x,w,h in stations:
    ring=[(0,h+.018),(.50*w,h+.015),(.87*w,h),(w,h-.075),(w,.55),(.91*w,.36),(0,.34),(-.91*w,.36),(-w,.55),(-w,h-.075),(-.87*w,h),(-.50*w,h+.015)]
    verts.extend((x,y,z) for y,z in ring)
faces=[]
for i in range(len(stations)-1):
    for j in range(12):faces.append((i*12+j,i*12+(j+1)%12,(i+1)*12+(j+1)%12,(i+1)*12+j))
faces.extend([tuple(reversed(range(12))),tuple((len(stations)-1)*12+j for j in range(12))])
shell=mesh('SM_Body_Sculpted_Shell',verts,faces,paint,body)
for x in (-1.36,1.36):
    cut=cylinder('CUT_Wheelarch',(x,0,.335),.374,2.6,plastic,None,axis='Y',vertices=64,bevel=0)
    boolean(shell,cut)
for loc,size in [((-.38,0,1.3),(2.18,1.48,1.3)),((1.42,0,1.14),(1.32,1.35,1.10))]:
    cut=box('CUT_Interior',loc,size,plastic,None,bevel=0);boolean(shell,cut)
bev=shell.modifiers.new('Small_Panel_Radii','BEVEL');bev.width=.014;bev.segments=3
bev=shell.modifiers.new('Correct_Panel_Normals','WEIGHTED_NORMAL');bev.keep_sharp=True

# Hood and separate roof/canopy assembly.
hood=mesh('SM_Hood',[(.74,-.73,1.024),(.74,.73,1.024),(1.95,.75,.895),(2.16,.67,.843),(2.16,-.67,.843),(1.95,-.75,.895)],[(0,1,2,3,4,5)],paint,body,solidify=.022)
roof=mesh('SM_Roof',[(-.94,-.67,1.405),(-.94,.67,1.405),(-.70,.69,1.445),(-.70,-.69,1.445),(.02,-.66,1.435),(.02,.66,1.435),(.18,.61,1.39),(.18,-.61,1.39)],[(0,1,2,3),(3,2,5,4),(4,5,6,7)],paint,canopy,solidify=.025)
mesh('SM_Windshield',[(.70,-.79,1.045),(.70,.79,1.045),(.16,.61,1.393),(.16,-.61,1.393)],[(0,1,2,3)],glass,canopy,solidify=.012)
mesh('SM_Rear_Windshield',[(-.95,-.66,1.399),(-.95,.66,1.399),(-1.67,.78,1.025),(-1.67,-.78,1.025)],[(0,1,2,3)],glass,canopy,solidify=.012)
for sign in (-1,1):
    side='L' if sign<0 else 'R'
    points=[(.68,sign*.80,1.045),(.12,sign*.665,1.391),(-.26,sign*.69,1.415),(-.26,sign*.842,1.045)]
    mesh('SM_Front_Window_'+side,points,[(0,1,2,3)],glass,canopy,solidify=.012)
    points=[(-.30,sign*.842,1.045),(-.30,sign*.69,1.415),(-.88,sign*.675,1.40),(-1.52,sign*.80,1.055)]
    mesh('SM_Rear_Window_'+side,points,[(0,1,2,3)],glass,canopy,solidify=.012)
    for name,pts,r in [('A',[(.72,sign*.82,1.02),(.16,sign*.655,1.40)],.025),('B',[(-.28,sign*.858,1.025),(-.28,sign*.70,1.418)],.018),('C',[(-1.63,sign*.80,1.015),(-.93,sign*.67,1.42)],.034)]:tube('SM_Pillar_'+name+'_'+side,pts,r,paint,canopy)
    tube('SM_Window_Chrome_'+side,[(.71,sign*.835,1.03),(-.28,sign*.866,1.027),(-1.62,sign*.821,1.02)],.007,alloy,canopy)
    # Door shutlines follow the body side, with a taut diagonal character crease.
    for x in (-.34,.77):tube('SM_Door_Seam_'+side+str(x),[(x,sign*.916,.97),(x-.03,sign*.918,.74),(x-.06,sign*.887,.42)],.003,plastic,body,6)
    tube('SM_Door_Rearline_'+side,[(-1.64,sign*.89,.98),(-1.72,sign*.907,.87),(-1.79,sign*.89,.73)],.003,plastic,body,6)
    tube('SM_Character_Line_'+side,[(.79,sign*.918,.92),(-.3,sign*.925,.64),(-1.8,sign*.90,.91)],.005,paint,body,6)
    box('SM_Door_Handle_F_'+side,(.06,sign*.919,.96),(.15,.025,.024),alloy,body,.009)
    box('SM_Door_Handle_R_'+side,(-1.02,sign*.919,.96),(.15,.025,.024),alloy,body,.009)
    box('SM_Rocker_'+side,(-.03,sign*.875,.395),(2.15,.07,.08),plastic,body,.02)
    tube('SM_Mirror_Arm_'+side,[(.56,sign*.82,1.06),(.50,sign*.98,1.07)],.021,plastic,body)
    box('SM_Mirror_'+side,(.47,sign*1.005,1.088),(.21,.145,.09),paint,body,.035)
    box('SM_Mirror_Glass_'+side,(.38,sign*1.007,1.09),(.012,.11,.052),alloy,body,.007)
    # Thin angular DRLs: recognizable modern sedan light signature, no badge.
    tube('SM_Headlight_'+side,[(2.322,sign*.12,.768),(2.30,sign*.59,.787),(2.14,sign*.78,.816)],.014,headlight,body)
    tube('SM_Tail_Light_'+side,[(-2.346,sign*.11,.868),(-2.31,sign*.64,.893),(-2.08,sign*.86,.928)],.016,taillight,body)

# Front grille slats and lower rear diffuser.
box('SM_Grille',(2.325,0,.582),(.035,1.40,.17),plastic,body,.03)
for i in range(3):box('SM_Grille_Slat_'+str(i),(2.350,0,.525+i*.045),(.024,1.33,.010),steel,body,.003)
for y in (-.55,-.27,0,.27,.55):box('SM_Grille_Vertical_'+str(y),(2.36,y,.58),(.022,.012,.135),plastic,body,.004)
box('SM_Front_Splitter',(2.24,0,.397),(.23,1.53,.045),plastic,body,.015)
box('SM_Rear_Diffuser',(-2.28,0,.445),(.13,1.50,.13),plastic,body,.018)
tube('SM_Tail_Connecting_LED',[(-2.354,-.55,.876),(-2.363,0,.873),(-2.354,.55,.876)],.006,taillight,body)

# Chassis, subframes, axles and exhaust, visible in the layered view.
box('SM_Floor_Pan',(-.21,0,.455),(2.8,1.43,.07),steel,chassis,.035)
for y in (-.51,.51):box('SM_Longitudinal_Rail_'+str(y),(.0,y,.38),(3.7,.075,.10),steel,chassis,.025)
for x in (-1.36,1.36):
    box('SM_Subframe_'+str(x),(x,0,.40),(.32,1.31,.10),plastic,chassis,.025)
    cylinder('SM_Axle_'+str(x),(x,0,.335),.035,1.62,steel,chassis,'Y',24)
tube('SM_Exhaust',[(1.18,-.20,.35),(.5,-.14,.29),(-.9,-.22,.28),(-2.25,-.43,.34)],.028,steel,chassis)
box('SM_Exhaust_Muffler',(-1.92,-.42,.34),(.43,.28,.13),steel,chassis,.05)

# A compact transverse inline-four and visible service components.
box('SM_Engine_Block',(1.22,0,.68),(.56,.64,.36),steel,power,.045)
box('SM_Engine_Cover',(1.21,.0,.889),(.57,.59,.08),plastic,power,.035)
for j in range(4):box('SM_Engine_Rib_'+str(j),(1.02+j*.12,0,.938),(.024,.43,.018),steel,power,.006)
cylinder('SM_Oil_Cap',(1.43,-.17,.952),.046,.025,plastic,power,'Z',24)
box('SM_Battery',(1.28,.51,.74),(.34,.23,.25),plastic,power,.015)
for y in (.44,.58):cylinder('SM_Battery_Terminal_'+str(y),(1.28,y,.88),.018,.025,steel,power,'Z',12)
box('SM_Airbox',(1.29,-.48,.78),(.41,.29,.20),plastic,power,.018)
for j in range(7):box('SM_Airbox_Rib_'+str(j),(1.12+j*.05,-.48,.888),(.012,.24,.012),steel,power,.003)
tube('SM_Intake_Hose',[(1.45,-.38,.79),(1.61,-.24,.79),(1.55,.05,.80)],.043,plastic,power)
box('SM_Radiator',(1.98,0,.63),(.055,1.12,.33),plastic,power,.012)
for j in range(13):box('SM_Radiator_Fin_'+str(j),(2.015,-.49+j*.082,.63),(.012,.013,.28),steel,power,.002)

# Seats, cabin floor, dashboard and steering wheel.
box('SM_Cabin_Floor',(-.32,0,.54),(2.02,1.38,.055),leather,interior,.025)
for y in (-.40,.40):
    box('SM_Front_Seat_Cushion_'+str(y),(-.12,y,.69),(.45,.43,.19),leather,interior,.065)
    box('SM_Front_Seat_Back_'+str(y),(-.37,y,.91),(.14,.43,.48),leather,interior,.055,rotation=(0,-.14,0))
    box('SM_Headrest_'+str(y),(-.40,y,1.17),(.13,.22,.16),leather,interior,.045)
box('SM_Rear_Seat_Cushion',(-1.03,0,.69),(.43,1.26,.16),leather,interior,.055)
box('SM_Rear_Seat_Back',(-1.24,0,.89),(.14,1.25,.39),leather,interior,.045)
box('SM_Dashboard',(.49,0,.966),(.27,1.36,.13),plastic,interior,.038)
box('SM_Center_Console',(.05,0,.724),(.70,.20,.25),plastic,interior,.025)
tube('SM_Steering_Column',[(.52,-.43,.90),(.32,-.43,1.00)],.025,plastic,interior)
points=[(.30, -.43+math.cos(j*2*math.pi/40)*.13, 1.0+math.sin(j*2*math.pi/40)*.13) for j in range(41)]
tube('SM_Steering_Rim',points,.015,leather,interior)
tube('SM_Steering_Spoke',[(.30,-.55,1),(.30,-.43,1),(.30,-.31,1)],.02,plastic,interior)

# Detailed wheels with split spokes, rotors and suspension: separate movable layers.
for x,axle_name in [(1.36,'F'),(-1.36,'R')]:
    for side,sign in [('L',-1),('R',1)]:
        wheel=layer('Layer_Wheel_'+axle_name+side,(0,sign*.67,0),'suspension')
        brake=layer('Layer_Brake_'+axle_name+side,(0,sign*.25,.06),'brakes')
        y=sign*.837;zc=.335
        # Lathed tire profile yields rounded shoulders and a clean rim opening.
        profile=[(.232,-.103),(.263,-.116),(.303,-.111),(.326,-.080),(.335,-.037),(.335,.037),(.326,.080),(.303,.111),(.263,.116),(.232,.103)]
        v=[];f=[];segments=64
        for radius,dy in profile:
            for j in range(segments):
                a=j*2*math.pi/segments;v.append((x+radius*math.cos(a),y+dy,zc+radius*math.sin(a)))
        for i in range(len(profile)):
            for j in range(segments):f.append((i*segments+j,i*segments+(j+1)%segments,((i+1)%len(profile))*segments+(j+1)%segments,((i+1)%len(profile))*segments+j))
        mesh('SM_Tire_'+axle_name+side,v,f,rubber,wheel)
        # Shallow concentric tread lines, no texture downloads.
        for dy in (-.055,.055):
            pts=[(x+.332*math.cos(j*math.pi/32),y+dy,zc+.332*math.sin(j*math.pi/32)) for j in range(65)]
            tube('SM_Tread_'+axle_name+side+str(dy),pts,.003,plastic,wheel,6)
        cylinder('SM_Rim_Barrel_'+axle_name+side,(x,y,zc),.237,.17,plastic,wheel,'Y',48,.006)
        outer_y=y+sign*.119
        # Annular rim border.
        for radius in (.231,.213):
            pts=[(x+radius*math.cos(j*math.pi/32),outer_y,zc+radius*math.sin(j*math.pi/32)) for j in range(65)]
            tube('SM_Rim_Lip_'+axle_name+side+str(radius),pts,.008,alloy,wheel)
        for j in range(5):
            angle=j*math.pi*2/5
            for delta in (-.08,.08):
                a=angle+delta
                p1=(x+.055*math.cos(angle+delta*.4),outer_y+.001*sign,zc+.055*math.sin(angle+delta*.4))
                p2=(x+.213*math.cos(a),outer_y,zc+.213*math.sin(a))
                tube('SM_Split_Spoke_'+axle_name+side+str(j)+str(delta),[p1,p2],.015,alloy,wheel,6)
        cylinder('SM_Wheel_Hub_'+axle_name+side,(x,outer_y,zc),.061,.025,alloy,wheel,'Y',32,.007)
        for j in range(5):
            a=j*math.pi*2/5
            cylinder('SM_Lug_'+axle_name+side+str(j),(x+.043*math.cos(a),outer_y+sign*.018,zc+.043*math.sin(a)),.008,.013,steel,wheel,'Y',8,.001)
        cylinder('SM_Brake_Disc_'+axle_name+side,(x,y-sign*.035,zc),.176,.028,steel,brake,'Y',48,.004)
        box('SM_Brake_Caliper_'+axle_name+side,(x+.13,y-sign*.022,zc+.035),(.075,.075,.19),red,brake,.018)
        cylinder('SM_Shock_'+axle_name+side,(x,y-sign*.15,.62),.032,.42,steel,chassis,'Z',24,.004)
        # Coil spring around the upright, with ends tied into its mount.
        pts=[]
        for j in range(113):
            a=j*math.pi/8;pts.append((x+.067*math.cos(a),y-sign*.15+.067*math.sin(a),.48+j/112*.28))
        tube('SM_Coil_'+axle_name+side,pts,.009,plastic,chassis,6)

# Apply modifiers and clean all exported meshes. Pure PBR colors need no UV textures.
meshes=[o for o in scene.objects if o.type=='MESH']
for obj in meshes:
    bpy.context.view_layer.objects.active=obj
    for mod_name in [m.name for m in obj.modifiers]:
        try:bpy.ops.object.modifier_apply(modifier=mod_name)
        except RuntimeError:pass
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000015)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    obj.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bpy.ops.object.select_all(action='DESELECT')

# Merge by layer and material, keeping animation depth while reducing draw calls.
for parent in layers.values():
    for mat in list(bpy.data.materials):
        members=[o for o in list(parent.children) if o.type=='MESH' and len(o.data.materials)==1 and o.data.materials[0]==mat]
        if len(members)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in members:o.select_set(True)
        bpy.context.view_layer.objects.active=members[0]
        bpy.ops.object.join();merged=bpy.context.object;merged.name='SM_'+parent.name.removeprefix('Layer_')+'_'+mat.name
        merged['category']=parent.get('category','')
        bm=bmesh.new();bm.from_mesh(merged.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bm.to_mesh(merged.data);bm.free()
bpy.ops.object.select_all(action='DESELECT')

# Accurate studio presentation, also used as the non-WebGL fallback.
scene.world=bpy.data.worlds.new('Studio_World');scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.72,.74,.76,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.3
def area(name,loc,power,size,target=(0,0,.7)):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc;obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
area('Studio_Key',(1,-4,6),700,5)
area('Studio_Fill',(-3,2,3),250,4)
area('Studio_Rim',(3,3,5),800,4)
data=bpy.data.cameras.new('Camera_Studio');camera=bpy.data.objects.new('Camera_Studio',data);scene.collection.objects.link(camera)
camera.location=(6.6,-6.2,3.8);camera.rotation_euler=(Vector((0,0,.7))-camera.location).to_track_quat('-Z','Y').to_euler();data.lens=62;scene.camera=camera
scene.render.resolution_x=1400;scene.render.resolution_y=850;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
scene.view_settings.view_transform='AgX'
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.filepath=str(OUT/'sedan-poster.png')

bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'unbranded-sedan.blend'))

# Run the required QA checker; planned independent layers are additionally audited per mesh.
sys.path.insert(0,str(Path.home()/'.agents/skills/blender-asset-qa/scripts'))
import qa_check
qa=qa_check.run(objects=[o.name for o in scene.objects if o.type=='MESH'],profile='game',eps=.00015,tol=.025,uv=False)
(REVIEW/'assembled-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')

bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type=='MESH' or obj.name.startswith('Layer_'):obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'unbranded-sedan.glb'),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False,export_animations=False,export_yup=True)
bpy.ops.render.render(write_still=True)

stats={'objects':sum(o.type=='MESH' for o in scene.objects),'triangles':sum(len(o.data.polygons) for o in scene.objects if o.type=='MESH'),'materials':len(bpy.data.materials),'layers':len(layers),'glb_bytes':(OUT/'unbranded-sedan.glb').stat().st_size,'qa_errors':qa['errors'],'qa_warnings':qa['warnings']}
(SOURCE/'model-report.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False))
