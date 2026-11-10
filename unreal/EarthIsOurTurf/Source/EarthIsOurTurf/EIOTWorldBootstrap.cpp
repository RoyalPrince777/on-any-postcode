#include "EIOTWorldBootstrap.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"

AEIOTWorldBootstrap::AEIOTWorldBootstrap()
{
    PrimaryActorTick.bCanEverTick=false;
    WorldServerBaseUrl=TEXT("http://127.0.0.1:8001");
}
void AEIOTWorldBootstrap::BeginPlay()
{
    Super::BeginPlay();
    FetchCells();
}
void AEIOTWorldBootstrap::FetchCells()
{
    const FString Url=FString::Printf(TEXT("%s/v1/world/cells?x=0&y=0&radius=%d"),*WorldServerBaseUrl,StreamRadius);
    TSharedRef<IHttpRequest,ESPMode::ThreadSafe> Request=FHttpModule::Get().CreateRequest();
    Request->SetURL(Url);
    Request->SetVerb(TEXT("GET"));
    Request->OnProcessRequestComplete().BindLambda([](FHttpRequestPtr Req,FHttpResponsePtr Resp,bool bOk)
    {
        if(!bOk || !Resp.IsValid() || Resp->GetResponseCode()!=200)
        {
            UE_LOG(LogTemp,Error,TEXT("EIOT world-cell request failed"));
            return;
        }
        UE_LOG(LogTemp,Log,TEXT("EIOT world cells loaded: %d bytes"),Resp->GetContentLength());
    });
    Request->ProcessRequest();
}
