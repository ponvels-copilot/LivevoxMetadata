namespace LivevoxMetadata.Models;

/// <summary>
/// Represents metadata for a Livevox campaign
/// </summary>
public class CampaignMetadata
{
    public int CampaignId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public DateTime CreatedDate { get; set; }
    public DateTime? ModifiedDate { get; set; }
    public bool IsActive { get; set; }
    public List<string> Tags { get; set; } = new List<string>();
}

/// <summary>
/// Represents metadata for a Livevox agent
/// </summary>
public class AgentMetadata
{
    public int AgentId { get; set; }
    public string Username { get; set; } = string.Empty;
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public List<int> CampaignIds { get; set; } = new List<int>();
    public bool IsActive { get; set; }
}

/// <summary>
/// Represents metadata for a Livevox call session
/// </summary>
public class CallSessionMetadata
{
    public string SessionId { get; set; } = string.Empty;
    public int CampaignId { get; set; }
    public int AgentId { get; set; }
    public DateTime StartTime { get; set; }
    public DateTime? EndTime { get; set; }
    public string CallDirection { get; set; } = string.Empty; // Inbound, Outbound
    public string CallResult { get; set; } = string.Empty;
    public Dictionary<string, object> CustomAttributes { get; set; } = new Dictionary<string, object>();
}
