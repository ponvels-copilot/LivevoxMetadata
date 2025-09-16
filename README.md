# LivevoxMetadata

A .NET Core C# library for handling Livevox metadata operations including campaigns, agents, and call sessions.

## Features

- **Campaign Metadata Management**: Create, retrieve, and update campaign metadata
- **Agent Metadata Management**: Manage agent information and campaign associations
- **Call Session Metadata**: Track call session information with custom attributes
- **Asynchronous Operations**: All operations are async/await compatible
- **In-Memory Storage**: Simple in-memory storage implementation (suitable for extension to database storage)

## Project Structure

```
LivevoxMetadata/
├── src/LivevoxMetadata/           # Main library project
│   ├── Models.cs                  # Data models for metadata entities
│   ├── IMetadataService.cs        # Service interface
│   └── MetadataService.cs         # Service implementation
├── tests/LivevoxMetadata.Tests/   # Unit tests
│   └── MetadataServiceTests.cs    # Comprehensive test suite
├── LivevoxMetadata.sln            # Solution file
└── README.md                      # This file
```

## Prerequisites

- .NET 8.0 or later
- Visual Studio 2022, Visual Studio Code, or any .NET-compatible IDE

## Building the Project

```bash
# Clone the repository
git clone https://github.com/ponvels-copilot/LivevoxMetadata.git
cd LivevoxMetadata

# Restore dependencies and build
dotnet restore
dotnet build

# Run tests
dotnet test
```

## Usage

### Basic Usage

```csharp
using LivevoxMetadata.Services;
using LivevoxMetadata.Models;

// Create service instance
IMetadataService metadataService = new MetadataService();

// Create campaign metadata
var campaign = new CampaignMetadata
{
    CampaignId = 1,
    Name = "Summer Promotion",
    Description = "Summer promotional campaign",
    CreatedDate = DateTime.UtcNow,
    IsActive = true,
    Tags = new List<string> { "promotion", "summer" }
};

await metadataService.CreateCampaignMetadataAsync(campaign);

// Retrieve campaign metadata
var retrievedCampaign = await metadataService.GetCampaignMetadataAsync(1);

// Create agent metadata
var agent = new AgentMetadata
{
    AgentId = 101,
    Username = "agent001",
    FirstName = "John",
    LastName = "Doe",
    Email = "john.doe@company.com",
    IsActive = true,
    CampaignIds = new List<int> { 1 }
};

await metadataService.CreateAgentMetadataAsync(agent);

// Create call session metadata
var callSession = new CallSessionMetadata
{
    SessionId = "session-12345",
    CampaignId = 1,
    AgentId = 101,
    StartTime = DateTime.UtcNow,
    CallDirection = "Outbound",
    CallResult = "Connected",
    CustomAttributes = new Dictionary<string, object>
    {
        { "priority", "high" },
        { "customerType", "premium" }
    }
};

await metadataService.CreateCallSessionMetadataAsync(callSession);
```

## API Reference

### Models

#### CampaignMetadata
- `CampaignId`: Unique identifier for the campaign
- `Name`: Campaign name
- `Description`: Campaign description
- `CreatedDate`: Creation timestamp
- `ModifiedDate`: Last modification timestamp
- `IsActive`: Active status flag
- `Tags`: List of tags for categorization

#### AgentMetadata
- `AgentId`: Unique identifier for the agent
- `Username`: Agent username
- `FirstName`: Agent first name
- `LastName`: Agent last name
- `Email`: Agent email address
- `CampaignIds`: List of associated campaign IDs
- `IsActive`: Active status flag

#### CallSessionMetadata
- `SessionId`: Unique session identifier
- `CampaignId`: Associated campaign ID
- `AgentId`: Associated agent ID
- `StartTime`: Call start timestamp
- `EndTime`: Call end timestamp (nullable)
- `CallDirection`: Direction (Inbound/Outbound)
- `CallResult`: Call outcome
- `CustomAttributes`: Dictionary for custom properties

### Service Methods

#### Campaign Operations
- `GetCampaignMetadataAsync(int campaignId)`: Retrieve campaign by ID
- `GetAllCampaignsAsync()`: Retrieve all campaigns
- `CreateCampaignMetadataAsync(CampaignMetadata metadata)`: Create new campaign
- `UpdateCampaignMetadataAsync(CampaignMetadata metadata)`: Update existing campaign

#### Agent Operations
- `GetAgentMetadataAsync(int agentId)`: Retrieve agent by ID
- `GetAllAgentsAsync()`: Retrieve all agents
- `CreateAgentMetadataAsync(AgentMetadata metadata)`: Create new agent

#### Call Session Operations
- `GetCallSessionMetadataAsync(string sessionId)`: Retrieve session by ID
- `CreateCallSessionMetadataAsync(CallSessionMetadata metadata)`: Create new session

## Testing

The project includes comprehensive unit tests covering all functionality:

```bash
# Run all tests
dotnet test

# Run tests with detailed output
dotnet test --logger:console --verbosity normal

# Run tests with coverage (requires additional tools)
dotnet test --collect:"XPlat Code Coverage"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add or update tests as needed
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.