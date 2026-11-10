using UnrealBuildTool;
public class EarthIsOurTurf : ModuleRules
{
    public EarthIsOurTurf(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage=PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[]{"Core","CoreUObject","Engine","InputCore","EnhancedInput","HTTP","Json","JsonUtilities","NavigationSystem"});
    }
}
