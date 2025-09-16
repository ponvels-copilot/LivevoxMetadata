using LivevoxMetadata.Models;
using LivevoxMetadata.Services;

namespace LivevoxMetadata.Tests;

public class MetadataServiceTests
{
    private readonly IMetadataService _metadataService;

    public MetadataServiceTests()
    {
        _metadataService = new MetadataService();
    }

    [Fact]
    public async Task CreateCampaignMetadata_ShouldReturnTrue_WhenValidMetadata()
    {
        // Arrange
        var campaign = new CampaignMetadata
        {
            CampaignId = 1,
            Name = "Test Campaign",
            Description = "Test Description",
            CreatedDate = DateTime.UtcNow,
            IsActive = true,
            Tags = new List<string> { "test", "campaign" }
        };

        // Act
        var result = await _metadataService.CreateCampaignMetadataAsync(campaign);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public async Task GetCampaignMetadata_ShouldReturnCampaign_WhenExists()
    {
        // Arrange
        var campaign = new CampaignMetadata
        {
            CampaignId = 2,
            Name = "Test Campaign 2",
            IsActive = true
        };
        await _metadataService.CreateCampaignMetadataAsync(campaign);

        // Act
        var result = await _metadataService.GetCampaignMetadataAsync(2);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Test Campaign 2", result.Name);
        Assert.True(result.IsActive);
    }

    [Fact]
    public async Task CreateAgentMetadata_ShouldReturnTrue_WhenValidMetadata()
    {
        // Arrange
        var agent = new AgentMetadata
        {
            AgentId = 1,
            Username = "agent001",
            FirstName = "John",
            LastName = "Doe",
            Email = "john.doe@example.com",
            IsActive = true,
            CampaignIds = new List<int> { 1, 2 }
        };

        // Act
        var result = await _metadataService.CreateAgentMetadataAsync(agent);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public async Task CreateCallSessionMetadata_ShouldReturnTrue_WhenValidMetadata()
    {
        // Arrange
        var session = new CallSessionMetadata
        {
            SessionId = "session-123",
            CampaignId = 1,
            AgentId = 1,
            StartTime = DateTime.UtcNow,
            CallDirection = "Outbound",
            CallResult = "Connected",
            CustomAttributes = new Dictionary<string, object> { { "priority", "high" } }
        };

        // Act
        var result = await _metadataService.CreateCallSessionMetadataAsync(session);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public async Task UpdateCampaignMetadata_ShouldUpdateModifiedDate_WhenValidUpdate()
    {
        // Arrange
        var campaign = new CampaignMetadata
        {
            CampaignId = 3,
            Name = "Original Name",
            CreatedDate = DateTime.UtcNow.AddDays(-1),
            IsActive = true
        };
        await _metadataService.CreateCampaignMetadataAsync(campaign);

        // Modify the campaign
        campaign.Name = "Updated Name";
        var beforeUpdate = DateTime.UtcNow;

        // Act
        var result = await _metadataService.UpdateCampaignMetadataAsync(campaign);
        var updated = await _metadataService.GetCampaignMetadataAsync(3);

        // Assert
        Assert.True(result);
        Assert.NotNull(updated);
        Assert.Equal("Updated Name", updated.Name);
        Assert.NotNull(updated.ModifiedDate);
        Assert.True(updated.ModifiedDate >= beforeUpdate);
    }
}