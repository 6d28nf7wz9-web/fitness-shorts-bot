"""Lightweight geometric gate for the procedural biceps teaching rig."""
import math
PIVOT=(0.0,0.0,1.35); ELBOW_RADII=(0.46,0.34,0.43); POSES=(0.0,-0.38,-0.92,-0.55,0.0)
BONE_ANCHORS={"radius":((-0.13,0.02,1.34),(-0.08,0.02,-1.02)),"ulna":((0.16,0.10,1.34),(0.11,0.10,-1.02))}
def rotate_y_about(point,pivot,angle):
 x,y,z=(point[i]-pivot[i] for i in range(3)); c,s=math.cos(angle),math.sin(angle)
 return (pivot[0]+x*c+z*s,pivot[1]+y,pivot[2]-x*s+z*c)
def normalized_joint_distance(point): return sum(((point[i]-PIVOT[i])/ELBOW_RADII[i])**2 for i in range(3))
def audit_geometry():
 issues=[]
 for bone,(proximal,distal) in BONE_ANCHORS.items():
  for index,angle in enumerate(POSES):
   p=rotate_y_about(proximal,PIVOT,angle)
   if normalized_joint_distance(p)>1: issues.append(f"{bone} proximal anchor escapes elbow at pose {index}: {p}")
   if math.dist(p,rotate_y_about(distal,PIVOT,angle))<1: issues.append(f"{bone} shaft collapsed at pose {index}")
 for angle in POSES:
  r=rotate_y_about(BONE_ANCHORS["radius"][1],PIVOT,angle); u=rotate_y_about(BONE_ANCHORS["ulna"][1],PIVOT,angle)
  if math.dist(r,u)<0.12: issues.append(f"radius/ulna converge at pose {angle}")
 return issues
