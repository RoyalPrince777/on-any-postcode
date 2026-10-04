#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EIOTWorldBootstrap.generated.h"

UCLASS()
class EARTHISOURTURF_API AEIOTWorldBootstrap : public AActor
{
    GENERATED_BODY()
public:
    AEIOTWorldBootstrap();
    virtual void BeginPlay() override;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="EIOT") FString WorldServerBaseUrl;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="EIOT") int32 StreamRadius=2;
private:
    void FetchCells();
};
