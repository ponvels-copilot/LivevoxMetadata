using LivevoxMetadata.Models;

namespace LivevoxMetadata.Services;

/// <summary>
/// Service for managing Livevox metadata operations
/// </summary>
public class MetadataService : IMetadataService
{
    private readonly Dictionary<int, CampaignMetadata> _campaigns;
    private readonly Dictionary<int, AgentMetadata> _agents;
    private readonly Dictionary<string, CallSessionMetadata> _callSessions;

    public MetadataService()
    {
        _campaigns = new Dictionary<int, CampaignMetadata>();
        _agents = new Dictionary<int, AgentMetadata>();
        _callSessions = new Dictionary<string, CallSessionMetadata>();
    }

    public Task<CampaignMetadata?> GetCampaignMetadataAsync(int campaignId)
    {
        _campaigns.TryGetValue(campaignId, out var campaign);
        return Task.FromResult(campaign);
    }

    public Task<IEnumerable<CampaignMetadata>> GetAllCampaignsAsync()
    {
        return Task.FromResult<IEnumerable<CampaignMetadata>>(_campaigns.Values);
    }

    public Task<bool> CreateCampaignMetadataAsync(CampaignMetadata metadata)
    {
        if (metadata == null || _campaigns.ContainsKey(metadata.CampaignId))
            return Task.FromResult(false);

        _campaigns[metadata.CampaignId] = metadata;
        return Task.FromResult(true);
    }

    public Task<bool> UpdateCampaignMetadataAsync(CampaignMetadata metadata)
    {
        if (metadata == null || !_campaigns.ContainsKey(metadata.CampaignId))
            return Task.FromResult(false);

        metadata.ModifiedDate = DateTime.UtcNow;
        _campaigns[metadata.CampaignId] = metadata;
        return Task.FromResult(true);
    }

    public Task<AgentMetadata?> GetAgentMetadataAsync(int agentId)
    {
        _agents.TryGetValue(agentId, out var agent);
        return Task.FromResult(agent);
    }

    public Task<IEnumerable<AgentMetadata>> GetAllAgentsAsync()
    {
        return Task.FromResult<IEnumerable<AgentMetadata>>(_agents.Values);
    }

    public Task<bool> CreateAgentMetadataAsync(AgentMetadata metadata)
    {
        if (metadata == null || _agents.ContainsKey(metadata.AgentId))
            return Task.FromResult(false);

        _agents[metadata.AgentId] = metadata;
        return Task.FromResult(true);
    }

    public Task<CallSessionMetadata?> GetCallSessionMetadataAsync(string sessionId)
    {
        _callSessions.TryGetValue(sessionId, out var session);
        return Task.FromResult(session);
    }

    public Task<bool> CreateCallSessionMetadataAsync(CallSessionMetadata metadata)
    {
        if (metadata == null || string.IsNullOrEmpty(metadata.SessionId) || _callSessions.ContainsKey(metadata.SessionId))
            return Task.FromResult(false);

        _callSessions[metadata.SessionId] = metadata;
        return Task.FromResult(true);
    }
}