#include "EIOTPedestrian.h"
AEIOTPedestrian::AEIOTPedestrian()
{
    PrimaryActorTick.bCanEverTick=true;
    AutoPossessAI=EAutoPossessAI::PlacedInWorldOrSpawned;
}
void AEIOTPedestrian::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const FVector Delta=LocalGoal-GetActorLocation();
    if(Delta.SizeSquared()>100.0f)
    {
        AddMovementInput(Delta.GetSafeNormal(),0.45f);
    }
}
