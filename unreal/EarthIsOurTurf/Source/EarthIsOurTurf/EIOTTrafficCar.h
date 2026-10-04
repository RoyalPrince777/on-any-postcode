#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "Components/StaticMeshComponent.h"
#include "EIOTTrafficCar.generated.h"

UCLASS()
class EARTHISOURTURF_API AEIOTTrafficCar : public APawn
{
    GENERATED_BODY()
public:
    AEIOTTrafficCar();
    virtual void Tick(float DeltaSeconds) override;
    UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Body;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="EIOT") float CruiseSpeedCmPerSecond=650.f;
};
