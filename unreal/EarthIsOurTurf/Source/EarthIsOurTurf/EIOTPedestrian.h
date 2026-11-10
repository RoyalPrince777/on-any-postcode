#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "EIOTPedestrian.generated.h"

UCLASS()
class EARTHISOURTURF_API AEIOTPedestrian : public ACharacter
{
    GENERATED_BODY()
public:
    AEIOTPedestrian();
    virtual void Tick(float DeltaSeconds) override;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="EIOT") FVector LocalGoal=FVector(500,0,0);
};
