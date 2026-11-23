"""Deterministic checks for forearm anchors and elbow flexion geometry."""
import math
PIVOT=(0.0,0.0,1.35)
POSES=(0.0,-0.38,-0.92,-0.55,0.0)
BONE_ANCHORS={"radius":((0.0,0.02,1.35),(-0.08,0.02,-1.02)),"ulna":((0.0,0.10,1.35),(0.11,0.10,-1.02))}
def rotate_y_about(point,pivot,angle):
 x,y,z=(point[i]-pivot[i] for i in range(3)); c,s=math.cos(angle),math.sin(angle)
 return (pivot[0]+x*c+z*s,pivot[1]+y,pivot[2]-x*s+z*c)
def audit_geometry():
 issues=[]
 for bone,(proximal,distal) in BONE_ANCHORS.items():
  if math.dist(proximal,PIVOT)>0.12: issues.append(f"{bone} proximal anchor is not seated on elbow flexion axis")
  for pose_index,angle in enumerate(POSES):
   p=rotate_y_about(proximal,PIVOT,angle); d=rotate_y_about(distal,PIVOT,angle)
   if math.dist(p,PIVOT)>0.12: issues.append(f"{bone} anchor drifts from pivot at pose {pose_index}")
   if math.dist(p,d)<1.0: issues.append(f"{bone} shaft collapsed at pose {pose_index}")
 for angle in POSES:
  r=rotate_y_about(BONE_ANCHORS["radius"][1],PIVOT,angle); u=rotate_y_about(BONE_ANCHORS["ulna"][1],PIVOT,angle)
  if math.dist(r,u)<0.12: issues.append(f"radius/ulna converge at pose {angle}")
 return issues
