using UnrealBuildTool;
using System.Collections.Generic;
public class EarthIsOurTurfTarget : TargetRules
{
    public EarthIsOurTurfTarget(TargetInfo Target) : base(Target)
    {
        Type=TargetType.Game;
        DefaultBuildSettings=BuildSettingsVersion.Latest;
        ExtraModuleNames.Add("EarthIsOurTurf");
    }
}
