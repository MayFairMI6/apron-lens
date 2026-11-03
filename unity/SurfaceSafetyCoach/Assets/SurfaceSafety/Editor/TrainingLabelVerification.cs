using System;
using System.Collections.Generic;
using UnityEngine;
using SurfaceSafety;

public static class TrainingLabelVerification {
    public static void Run(){
        Action<bool,string> check=(ok,name)=>{if(!ok)throw new Exception("Training labels: "+name);};
        foreach(var bounds in new[]{new Rect(40,144,936,549),new Rect(22.5f,944,850.5f,344)}){
            var used=new List<Rect>();var size=new Vector2(125,39);var anchor=bounds.center;
            // Coincident projections are the observed wide-overview failure. Selection is
            // placed first; all subsequent visible tags must stay separated and in scene.
            var slots=new List<int>();var rects=new List<Rect>();
            for(int i=0;i<4;i++){
                check(TrainingLabelLayout.Place(anchor,size,bounds,used,i==0?0:-1,false,out var rect,out var slot),"four clustered aircraft fit");
                check(bounds.Contains(rect.min)&&bounds.Contains(rect.max-Vector2.one*.001f),"full label inside safe view");
                foreach(var previous in used)check(!previous.Overlaps(rect),"no overlapping aircraft tags");
                used.Add(rect);rects.Add(rect);slots.Add(slot);
            }
            check(slots[0]==0,"selected label owns default position");
            used.Clear();
            for(int i=0;i<4;i++){
                check(TrainingLabelLayout.Place(anchor+Vector2.one*.1f,size,bounds,used,slots[i],true,out var rect,out var slot),"small pan keeps visible labels");
                check(slot==slots[i],"small pan preserves placement slot");used.Add(rect);
            }
            bool vehicle=TrainingLabelLayout.Place(anchor,new Vector2(190,36),bounds,used,-1,false,out var vehicleRect,out _);
            if(vehicle)foreach(var rect in used)check(!rect.Overlaps(vehicleRect),"vehicle shares collision occupancy");
            // Off-centre projections clamp complete tags, never text into the side panel.
            check(TrainingLabelLayout.Place(bounds.max,size,bounds,new List<Rect>(),0,true,out var edge,out _),"edge placement");
            check(edge.xMax<=bounds.xMax&&edge.yMax<=bounds.yMax,"edge clamp");
        }
        var tiny=new Rect(0,0,125,39);var packed=new List<Rect>{tiny};
        check(!TrainingLabelLayout.Place(tiny.center,new Vector2(125,39),tiny,packed,-1,false,out _,out _),"lower priority tag hidden when no room");
        check(TrainingLabelLayout.Place(tiny.center,new Vector2(125,39),tiny,new List<Rect>(),0,true,out _,out _),"selected remains visible in tight view");
        var wide=new Rect(0,0,900,500);var separated=new List<Rect>();
        foreach(var p in new[]{new Vector2(100,100),new Vector2(350,100),new Vector2(600,100),new Vector2(750,300)}){
            check(TrainingLabelLayout.Place(p,new Vector2(125,39),wide,separated,0,false,out var rect,out var slot)&&slot==0,"separated tags allow ordinary placement");separated.Add(rect);
        }
        Debug.Log("TRAINING_LABEL_CHECKS_PASS");
    }
}
