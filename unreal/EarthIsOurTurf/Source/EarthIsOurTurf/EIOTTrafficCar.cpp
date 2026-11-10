#include "EIOTTrafficCar.h"
AEIOTTrafficCar::AEIOTTrafficCar()
{
    PrimaryActorTick.bCanEverTick=true;
    Body=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
    SetRootComponent(Body);
}
void AEIOTTrafficCar::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    AddActorWorldOffset(GetActorForwardVector()*CruiseSpeedCmPerSecond*DeltaSeconds,true);
}
