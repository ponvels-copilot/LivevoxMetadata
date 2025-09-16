using LivevoxMetadata.Models;

namespace LivevoxMetadata.Services;

/// <summary>
/// Interface for Livevox metadata operations
/// </summary>
public interface IMetadataService
{
    // Campaign operations
    Task<CampaignMetadata?> GetCampaignMetadataAsync(int campaignId);
    Task<IEnumerable<CampaignMetadata>> GetAllCampaignsAsync();
    Task<bool> CreateCampaignMetadataAsync(CampaignMetadata metadata);
    Task<bool> UpdateCampaignMetadataAsync(CampaignMetadata metadata);

    // Agent operations
    Task<AgentMetadata?> GetAgentMetadataAsync(int agentId);
    Task<IEnumerable<AgentMetadata>> GetAllAgentsAsync();
    Task<bool> CreateAgentMetadataAsync(AgentMetadata metadata);

    // Call session operations
    Task<CallSessionMetadata?> GetCallSessionMetadataAsync(string sessionId);
    Task<bool> CreateCallSessionMetadataAsync(CallSessionMetadata metadata);
}