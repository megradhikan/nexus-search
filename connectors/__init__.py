from connectors.github import GitHubConnector
from connectors.notion import NotionConnector

ConnectorRegistry = {
    "github": GitHubConnector,
    "notion": NotionConnector,
}
