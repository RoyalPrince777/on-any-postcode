using UnrealBuildTool;
using System.Collections.Generic;
public class EarthIsOurTurfServerTarget : TargetRules
{
    public EarthIsOurTurfServerTarget(TargetInfo Target) : base(Target)
    {
        Type=TargetType.Server;
        DefaultBuildSettings=BuildSettingsVersion.Latest;
        ExtraModuleNames.Add("EarthIsOurTurf");
    }
}
