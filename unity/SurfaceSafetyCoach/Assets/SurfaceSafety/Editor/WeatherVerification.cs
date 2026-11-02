using System;
using UnityEngine;
using SurfaceSafety;

public static class WeatherVerification {
    public static void Run(){
        int n=0;Action<bool,string> check=(ok,label)=>{if(!ok)throw new Exception("Weather check: "+label);n++;};
        var plan=new TrainingEnvironment{version=1,kind="rain",frames=new[]{
            new EnvironmentFrame{t=0,precipitation=.1f,daylight=1},
            new EnvironmentFrame{t=3600,precipitation=.9f,daylight=.1f}}};
        TrainingWeather.Validate(plan,3600);
        check(Mathf.Abs(TrainingWeather.At(plan,1800).precipitation-.5f)<.001f,"source-time interpolation");
        check(TrainingWeather.At(null,100).daylight==1,"legacy scene retains daylight");
        TrainingWeather.Validate(new TrainingEnvironment(),3600);
        check(TrainingWeather.At(new TrainingEnvironment(),100).daylight==1,"JsonUtility empty optional object retains daylight");
        var original=TrainingWeather.ParticlePosition(8,250,false,1.8f,60);
        check(original==TrainingWeather.ParticlePosition(8,250,false,1.8f,60),"same source time freezes rain");
        check(original!=TrainingWeather.ParticlePosition(8,250.1f,false,1.8f,60),"advanced source time moves rain");
        check(TrainingWeather.ParticlePosition(8,250,true,1.8f,60)!=original,"snow has distinct fall behavior");
        check(Mathf.Abs(TrainingWeather.At(plan,3500).daylight-.125f)<.001f,"daylight follows source time");
        plan.version=2;bool rejected=false;try{TrainingWeather.Validate(plan,3600);}catch(ArgumentException){rejected=true;}
        check(rejected,"unsupported version rejected");plan.version=1;
        plan.frames[1].t=float.NaN;rejected=false;try{TrainingWeather.Validate(plan,3600);}catch(ArgumentException){rejected=true;}
        check(rejected,"invalid environment timing rejected");
        Debug.Log("WEATHER_CLIENT_CHECKS_PASS: "+n);
    }
}
