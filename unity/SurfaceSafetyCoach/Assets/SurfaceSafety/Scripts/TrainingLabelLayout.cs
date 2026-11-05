using System.Collections.Generic;
using UnityEngine;

namespace SurfaceSafety {
    // Canvas-local, bounded placement. Call in priority order; never move scene objects.
    public static class TrainingLabelLayout {
        static readonly Vector2[] Slots={Vector2.zero,new Vector2(0,1),new Vector2(0,-1),
            new Vector2(1,0),new Vector2(-1,0),new Vector2(0,2),new Vector2(0,-2)};
        public static bool Place(Vector2 anchor,Vector2 size,Rect bounds,IList<Rect> occupied,
            int preferredSlot,bool wasVisible,out Rect placed,out int slot){
            placed=new Rect();slot=-1;
            if(bounds.width<size.x||bounds.height<size.y)return false;
            // A hidden tag needs a little extra clearance before returning. Existing tags
            // retain their slot while valid, avoiding swaps on tiny camera movements.
            float gap=wasVisible?6:12;
            for(int attempt=-1;attempt<Slots.Length;attempt++){
                int candidate=attempt<0?preferredSlot:attempt;
                if(candidate<0||candidate>=Slots.Length||(attempt>=0&&candidate==preferredSlot))continue;
                var offset=Vector2.Scale(Slots[candidate],size+Vector2.one*14);
                var rect=new Rect(anchor.x-size.x*.5f+offset.x,anchor.y+offset.y,size.x,size.y);
                rect.x=Mathf.Clamp(rect.x,bounds.xMin,bounds.xMax-size.x);
                rect.y=Mathf.Clamp(rect.y,bounds.yMin,bounds.yMax-size.y);
                bool collision=false;
                var padded=new Rect(rect.x-gap,rect.y-gap,rect.width+2*gap,rect.height+2*gap);
                foreach(var other in occupied)if(padded.Overlaps(other)){collision=true;break;}
                if(collision)continue;
                placed=rect;slot=candidate;return true;
            }
            return false;
        }
    }
}
