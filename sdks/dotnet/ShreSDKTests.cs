using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Moq;
using Moq.Protected;
using Xunit;
using ShreAI.Sdk;


namespace ShreAI.Sdk.Tests
{
    /// <summary>
    /// Contract tests for Shre SDK v2.0.0
    ///
    /// Validates all 4 locked endpoints:
    /// 1. POST /v1/events/batch
    /// 2. POST /v1/sdk/session
    /// 3. GET /v1/sdk/config
    /// 4. POST /v1/sdk/heartbeat
    ///
    /// Test contract adherence across success, error, and edge cases.
    /// </summary>
    public class ShreSDKTests
    {
        private readonly string _baseUrl = "https://apiauth.shre.ai";
        private readonly string _tenantId = "test-workspace-123";
        private readonly string _appPlatform = "dotnet";

        #region Fixtures

        private ShreSDK CreateSDK(HttpClient? httpClient = null)
        {
            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            if (httpClient != null)
            {
                // Replace the internal HttpClient via reflection if needed
                // For now, we use the standard approach with mocked handlers
            }
            return sdk;
        }

        private Mock<HttpMessageHandler> CreateMockHandler(HttpStatusCode statusCode, string responseContent)
        {
            var mockHandler = new Mock<HttpMessageHandler>();
            var response = new HttpResponseMessage
            {
                StatusCode = statusCode,
                Content = new StringContent(responseContent, Encoding.UTF8, "application/json")
            };

            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<System.Threading.CancellationToken>()
                )
                .ReturnsAsync(response);

            return mockHandler;
        }

        #endregion

        #region POST /v1/events/batch Tests

        [Fact]
        public async Task SendEventsBatchAsync_Success_SingleEvent()
        {
            // Arrange
            var responseData = JsonSerializer.Serialize(new
            {
                accepted = 1,
                rejected = 0,
                trackingEnabled = true,
                nextFlushSeconds = 30
            });
            var mockHandler = CreateMockHandler(HttpStatusCode.OK, responseData);
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            // Reflection to inject mock HttpClient
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            var events = new List<Event>
            {
                new Event { EventId = "evt_001", EventName = "page_view", EntityType = "page" }
            };

            // Act
            var result = await sdk.SendEventsBatchAsync(events);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(1, result.Accepted);
            Assert.Equal(0, result.Rejected);
            Assert.True(result.TrackingEnabled);
            Assert.Equal(30, result.NextFlushSeconds);

            // Verify request was made
            mockHandler.Protected().Verify(
                "SendAsync",
                Times.Once(),
                ItExpr.IsAny<HttpRequestMessage>(),
                ItExpr.IsAny<System.Threading.CancellationToken>()
            );
        }

        [Fact]
        public async Task SendEventsBatchAsync_Success_MultipleEvents()
        {
            // Arrange
            var responseData = JsonSerializer.Serialize(new
            {
                accepted = 3,
                rejected = 0,
                trackingEnabled = true,
                nextFlushSeconds = 30
            });
            var mockHandler = CreateMockHandler(HttpStatusCode.OK, responseData);
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            var events = new List<Event>
            {
                new Event { EventId = "evt_001", EventName = "page_view", EntityType = "page" },
                new Event { EventId = "evt_002", EventName = "button_click", EntityType = "button" },
                new Event { EventId = "evt_003", EventName = "form_submit", EntityType = "form" }
            };

            // Act
            var result = await sdk.SendEventsBatchAsync(events);

            // Assert
            Assert.Equal(3, result.Accepted);
            Assert.Equal(0, result.Rejected);
        }

        [Fact]
        public async Task SendEventsBatchAsync_WithOptionalFields()
        {
            // Arrange
            var responseData = JsonSerializer.Serialize(new
            {
                accepted = 1,
                rejected = 0,
                trackingEnabled = true,
                nextFlushSeconds = 30
            });
            var mockHandler = CreateMockHandler(HttpStatusCode.OK, responseData);
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            var now = DateTime.UtcNow;
            var events = new List<Event>
            {
                new Event
                {
                    EventId = "evt_001",
                    EventName = "purchase",
                    EntityType = "transaction",
                    EntityId = "txn_123",
                    Timestamp = now,
                    Metadata = new Dictionary<string, object> { { "amount", 99.99 }, { "currency", "USD" } }
                }
            };

            // Act
            var result = await sdk.SendEventsBatchAsync(events);

            // Assert
            Assert.Equal(1, result.Accepted);
        }

        [Fact]
        public async Task SendEventsBatchAsync_IncludesRequiredHeaders()
        {
            // Arrange
            var capturedRequest = (HttpRequestMessage?)null;
            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<System.Threading.CancellationToken>()
                )
                .Callback<HttpRequestMessage, System.Threading.CancellationToken>((req, _) => capturedRequest = req)
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = HttpStatusCode.OK,
                    Content = new StringContent(JsonSerializer.Serialize(new
                    {
                        accepted = 1,
                        rejected = 0,
                        trackingEnabled = true,
                        nextFlushSeconds = 30
                    }), Encoding.UTF8, "application/json")
                });

            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };
            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            var events = new List<Event> { new Event { EventId = "evt_001", EventName = "test", EntityType = "test" } };

            // Act
            await sdk.SendEventsBatchAsync(events);

            // Assert
            Assert.NotNull(capturedRequest);
            Assert.True(capturedRequest.Headers.Contains("x-shre-tenant"));
            Assert.True(capturedRequest.Headers.Contains("x-shre-app"));
            Assert.Equal("test-workspace-123", capturedRequest.Headers.GetValues("x-shre-tenant").First());
            Assert.Equal("dotnet", capturedRequest.Headers.GetValues("x-shre-app").First());
        }

        [Fact]
        public async Task SendEventsBatchAsync_NoAuthorizationRequired()
        {
            // Arrange
            var capturedRequest = (HttpRequestMessage?)null;
            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<System.Threading.CancellationToken>()
                )
                .Callback<HttpRequestMessage, System.Threading.CancellationToken>((req, _) => capturedRequest = req)
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = HttpStatusCode.OK,
                    Content = new StringContent(JsonSerializer.Serialize(new
                    {
                        accepted = 1,
                        rejected = 0,
                        trackingEnabled = true,
                        nextFlushSeconds = 30
                    }), Encoding.UTF8, "application/json")
                });

            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };
            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            var events = new List<Event> { new Event { EventId = "evt_001", EventName = "test", EntityType = "test" } };

            // Act
            await sdk.SendEventsBatchAsync(events);

            // Assert
            Assert.NotNull(capturedRequest);
            Assert.False(capturedRequest.Headers.Contains("Authorization"));
        }

        [Fact]
        public async Task SendEventsBatchAsync_EmptyEventList()
        {
            // Arrange
            var responseData = JsonSerializer.Serialize(new
            {
                accepted = 0,
                rejected = 0,
                trackingEnabled = true,
                nextFlushSeconds = 30
            });
            var mockHandler = CreateMockHandler(HttpStatusCode.OK, responseData);
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            var result = await sdk.SendEventsBatchAsync(new List<Event>());

            // Assert
            Assert.Equal(0, result.Accepted);
        }

        [Fact]
        public async Task SendEventsBatchAsync_BadRequest400()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.BadRequest, "Missing required header");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            var events = new List<Event> { new Event { EventId = "evt_001", EventName = "test", EntityType = "test" } };

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.SendEventsBatchAsync(events));
        }

        [Fact]
        public async Task SendEventsBatchAsync_Unauthorized401()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.Unauthorized, "Invalid JWT or bootstrap key");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            var events = new List<Event> { new Event { EventId = "evt_001", EventName = "test", EntityType = "test" } };

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.SendEventsBatchAsync(events));
        }

        [Fact]
        public async Task SendEventsBatchAsync_ServerError500()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.InternalServerError, "Internal server error");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            var events = new List<Event> { new Event { EventId = "evt_001", EventName = "test", EntityType = "test" } };

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.SendEventsBatchAsync(events));
        }

        #endregion

        #region POST /v1/sdk/session Tests

        [Fact]
        public async Task CreateSessionAsync_Success()
        {
            // Arrange
            var responseData = JsonSerializer.Serialize(new
            {
                accessToken = "jwt_token_xyz789",
                expiresIn = 3600,
                tokenType = "Bearer"
            });
            var mockHandler = CreateMockHandler(HttpStatusCode.OK, responseData);
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            var result = await sdk.CreateSessionAsync("pub_key_abc123");

            // Assert
            Assert.NotNull(result);
            Assert.Equal("jwt_token_xyz789", result.AccessToken);
            Assert.Equal(3600, result.ExpiresIn);
            Assert.Equal("Bearer", result.TokenType);
        }

        [Fact]
        public async Task CreateSessionAsync_StoresToken()
        {
            // Arrange
            var responseData = JsonSerializer.Serialize(new
            {
                accessToken = "jwt_token_xyz789",
                expiresIn = 3600,
                tokenType = "Bearer"
            });
            var mockHandler = CreateMockHandler(HttpStatusCode.OK, responseData);
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            await sdk.CreateSessionAsync("pub_key_abc123");

            // Assert
            // Token should be stored (verify via reflection if needed)
            var tokenFieldInfo = typeof(ShreSDK).GetField("_authToken", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            var storedToken = tokenFieldInfo?.GetValue(sdk);
            Assert.Equal("jwt_token_xyz789", storedToken);
        }

        [Fact]
        public async Task CreateSessionAsync_IncludesRequiredHeaders()
        {
            // Arrange
            var capturedRequest = (HttpRequestMessage?)null;
            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<System.Threading.CancellationToken>()
                )
                .Callback<HttpRequestMessage, System.Threading.CancellationToken>((req, _) => capturedRequest = req)
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = HttpStatusCode.OK,
                    Content = new StringContent(JsonSerializer.Serialize(new
                    {
                        accessToken = "jwt_token_xyz789",
                        expiresIn = 3600,
                        tokenType = "Bearer"
                    }), Encoding.UTF8, "application/json")
                });

            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };
            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            var bootstrapKey = "pub_key_abc123";

            // Act
            await sdk.CreateSessionAsync(bootstrapKey);

            // Assert
            Assert.NotNull(capturedRequest);
            Assert.True(capturedRequest.Headers.Contains("x-shre-tenant"));
            Assert.True(capturedRequest.Headers.Contains("x-shre-app"));
            Assert.Equal("test-workspace-123", capturedRequest.Headers.GetValues("x-shre-tenant").First());
            Assert.Equal("pub_key_abc123", capturedRequest.Headers.GetValues("x-shre-app").First());
        }

        [Fact]
        public async Task CreateSessionAsync_Unauthorized401()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.Unauthorized, "Invalid bootstrap key");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.CreateSessionAsync("invalid_key"));
        }

        [Fact]
        public async Task CreateSessionAsync_BadRequest400()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.BadRequest, "Missing x-shre-tenant header");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.CreateSessionAsync("pub_key_abc123"));
        }

        [Fact]
        public async Task CreateSessionAsync_ServerError500()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.InternalServerError, "Internal server error");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.CreateSessionAsync("pub_key_abc123"));
        }

        #endregion

        #region GET /v1/sdk/config Tests

        [Fact]
        public async Task GetConfigAsync_Success()
        {
            // Arrange
            var responseData = JsonSerializer.Serialize(new
            {
                trackingEnabled = true,
                disabledEvents = new List<string> { },
                piiMasking = false,
                maxQueueSize = 100,
                flushIntervalSeconds = 30,
                batchSize = 10,
                sinkConfigured = true
            });
            var mockHandler = CreateMockHandler(HttpStatusCode.OK, responseData);
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            var result = await sdk.GetConfigAsync();

            // Assert
            Assert.NotNull(result);
            Assert.True(result.TrackingEnabled);
            Assert.Empty(result.DisabledEvents);
            Assert.False(result.PiiMasking);
            Assert.Equal(100, result.MaxQueueSize);
            Assert.Equal(30, result.FlushIntervalSeconds);
            Assert.Equal(10, result.BatchSize);
            Assert.True(result.SinkConfigured);
        }

        [Fact]
        public async Task GetConfigAsync_WithDisabledEvents()
        {
            // Arrange
            var responseData = JsonSerializer.Serialize(new
            {
                trackingEnabled = true,
                disabledEvents = new List<string> { "page_view", "button_click" },
                piiMasking = true,
                maxQueueSize = 100,
                flushIntervalSeconds = 30,
                batchSize = 10,
                sinkConfigured = true
            });
            var mockHandler = CreateMockHandler(HttpStatusCode.OK, responseData);
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            var result = await sdk.GetConfigAsync();

            // Assert
            Assert.Equal(2, result.DisabledEvents.Count);
            Assert.Contains("page_view", result.DisabledEvents);
        }

        [Fact]
        public async Task GetConfigAsync_IncludesRequiredHeaders()
        {
            // Arrange
            var capturedRequest = (HttpRequestMessage?)null;
            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<System.Threading.CancellationToken>()
                )
                .Callback<HttpRequestMessage, System.Threading.CancellationToken>((req, _) => capturedRequest = req)
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = HttpStatusCode.OK,
                    Content = new StringContent(JsonSerializer.Serialize(new
                    {
                        trackingEnabled = true,
                        disabledEvents = new List<string> { },
                        piiMasking = false,
                        maxQueueSize = 100,
                        flushIntervalSeconds = 30,
                        batchSize = 10,
                        sinkConfigured = true
                    }), Encoding.UTF8, "application/json")
                });

            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };
            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            await sdk.GetConfigAsync();

            // Assert
            Assert.NotNull(capturedRequest);
            Assert.True(capturedRequest.Headers.Contains("x-shre-tenant"));
            Assert.Equal("test-workspace-123", capturedRequest.Headers.GetValues("x-shre-tenant").First());
        }

        [Fact]
        public async Task GetConfigAsync_UsesGetMethod()
        {
            // Arrange
            var capturedRequest = (HttpRequestMessage?)null;
            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<System.Threading.CancellationToken>()
                )
                .Callback<HttpRequestMessage, System.Threading.CancellationToken>((req, _) => capturedRequest = req)
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = HttpStatusCode.OK,
                    Content = new StringContent(JsonSerializer.Serialize(new
                    {
                        trackingEnabled = true,
                        disabledEvents = new List<string> { },
                        piiMasking = false,
                        maxQueueSize = 100,
                        flushIntervalSeconds = 30,
                        batchSize = 10,
                        sinkConfigured = true
                    }), Encoding.UTF8, "application/json")
                });

            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };
            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            await sdk.GetConfigAsync();

            // Assert
            Assert.NotNull(capturedRequest);
            Assert.Equal(HttpMethod.Get, capturedRequest.Method);
        }

        [Fact]
        public async Task GetConfigAsync_Unauthorized401()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.Unauthorized, "Invalid tenant");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.GetConfigAsync());
        }

        [Fact]
        public async Task GetConfigAsync_BadRequest400()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.BadRequest, "Missing x-shre-tenant header");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.GetConfigAsync());
        }

        [Fact]
        public async Task GetConfigAsync_ServerError500()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.InternalServerError, "Internal server error");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.GetConfigAsync());
        }

        #endregion

        #region POST /v1/sdk/heartbeat Tests

        [Fact]
        public async Task SendHeartbeatAsync_Success()
        {
            // Arrange
            var responseData = JsonSerializer.Serialize(new
            {
                ok = true,
                serverTime = "2026-05-02T12:00:00Z"
            });
            var mockHandler = CreateMockHandler(HttpStatusCode.OK, responseData);
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            var result = await sdk.SendHeartbeatAsync("device_123", 5, 10);

            // Assert
            Assert.NotNull(result);
            Assert.True(result.Ok);
            Assert.Equal("2026-05-02T12:00:00Z", result.ServerTime);
        }

        [Fact]
        public async Task SendHeartbeatAsync_DefaultEventsSent()
        {
            // Arrange
            var capturedRequest = (HttpRequestMessage?)null;
            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<System.Threading.CancellationToken>()
                )
                .Callback<HttpRequestMessage, System.Threading.CancellationToken>((req, _) => capturedRequest = req)
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = HttpStatusCode.OK,
                    Content = new StringContent(JsonSerializer.Serialize(new
                    {
                        ok = true,
                        serverTime = "2026-05-02T12:00:00Z"
                    }), Encoding.UTF8, "application/json")
                });

            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };
            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            await sdk.SendHeartbeatAsync("device_123", 5);

            // Assert
            Assert.NotNull(capturedRequest);
            var content = await capturedRequest.Content.ReadAsStringAsync();
            var json = JsonSerializer.Deserialize<JsonElement>(content);
            Assert.Equal(0, json.GetProperty("eventsSent").GetInt32());
        }

        [Fact]
        public async Task SendHeartbeatAsync_IncludesRequiredHeaders()
        {
            // Arrange
            var capturedRequest = (HttpRequestMessage?)null;
            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<System.Threading.CancellationToken>()
                )
                .Callback<HttpRequestMessage, System.Threading.CancellationToken>((req, _) => capturedRequest = req)
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = HttpStatusCode.OK,
                    Content = new StringContent(JsonSerializer.Serialize(new
                    {
                        ok = true,
                        serverTime = "2026-05-02T12:00:00Z"
                    }), Encoding.UTF8, "application/json")
                });

            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };
            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            await sdk.SendHeartbeatAsync("device_123", 5);

            // Assert
            Assert.NotNull(capturedRequest);
            Assert.True(capturedRequest.Headers.Contains("x-shre-tenant"));
            Assert.True(capturedRequest.Headers.Contains("x-shre-app"));
            Assert.Equal("test-workspace-123", capturedRequest.Headers.GetValues("x-shre-tenant").First());
            Assert.Equal("dotnet", capturedRequest.Headers.GetValues("x-shre-app").First());
        }

        [Fact]
        public async Task SendHeartbeatAsync_IncludesPayloadFields()
        {
            // Arrange
            var capturedRequest = (HttpRequestMessage?)null;
            var mockHandler = new Mock<HttpMessageHandler>();
            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<System.Threading.CancellationToken>()
                )
                .Callback<HttpRequestMessage, System.Threading.CancellationToken>((req, _) => capturedRequest = req)
                .ReturnsAsync(new HttpResponseMessage
                {
                    StatusCode = HttpStatusCode.OK,
                    Content = new StringContent(JsonSerializer.Serialize(new
                    {
                        ok = true,
                        serverTime = "2026-05-02T12:00:00Z"
                    }), Encoding.UTF8, "application/json")
                });

            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };
            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            await sdk.SendHeartbeatAsync("device_123", 5, 10);

            // Assert
            Assert.NotNull(capturedRequest);
            var content = await capturedRequest.Content.ReadAsStringAsync();
            var json = JsonSerializer.Deserialize<JsonElement>(content);
            Assert.Equal("test-workspace-123", json.GetProperty("tenantId").GetString());
            Assert.Equal("dotnet", json.GetProperty("app").GetString());
            Assert.Equal("device_123", json.GetProperty("deviceId").GetString());
            Assert.Equal(5, json.GetProperty("eventsQueued").GetInt32());
            Assert.Equal(10, json.GetProperty("eventsSent").GetInt32());
        }

        [Fact]
        public async Task SendHeartbeatAsync_ZeroEvents()
        {
            // Arrange
            var responseData = JsonSerializer.Serialize(new
            {
                ok = true,
                serverTime = "2026-05-02T12:00:00Z"
            });
            var mockHandler = CreateMockHandler(HttpStatusCode.OK, responseData);
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            var result = await sdk.SendHeartbeatAsync("device_123", 0, 0);

            // Assert
            Assert.True(result.Ok);
        }

        [Fact]
        public async Task SendHeartbeatAsync_BadRequest400()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.BadRequest, "Invalid payload");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.SendHeartbeatAsync("device_123", 5));
        }

        [Fact]
        public async Task SendHeartbeatAsync_Unauthorized401()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.Unauthorized, "Invalid tenant");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.SendHeartbeatAsync("device_123", 5));
        }

        [Fact]
        public async Task SendHeartbeatAsync_ServerError502()
        {
            // Arrange
            var mockHandler = CreateMockHandler(HttpStatusCode.BadGateway, "Bad gateway");
            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };

            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act & Assert
            await Assert.ThrowsAsync<ShreException>(() => sdk.SendHeartbeatAsync("device_123", 5));
        }

        #endregion

        #region Integration Tests

        [Fact]
        public async Task FullWorkflow_ReadMode()
        {
            // Arrange
            var mockHandler = new Mock<HttpMessageHandler>();
            var callCount = 0;

            mockHandler
                .Protected()
                .Setup<Task<HttpResponseMessage>>(
                    "SendAsync",
                    ItExpr.IsAny<HttpRequestMessage>(),
                    ItExpr.IsAny<System.Threading.CancellationToken>()
                )
                .ReturnsAsync(new HttpResponseMessage { StatusCode = HttpStatusCode.OK, Content = new StringContent("") })
                .Callback<HttpRequestMessage, System.Threading.CancellationToken>((req, _) =>
                {
                    callCount++;
                    if (callCount == 1)
                    {
                        // Config response
                        req.Content = new StringContent(JsonSerializer.Serialize(new
                        {
                            trackingEnabled = true,
                            disabledEvents = new List<string> { },
                            piiMasking = false,
                            maxQueueSize = 100,
                            flushIntervalSeconds = 30,
                            batchSize = 10,
                            sinkConfigured = true
                        }), Encoding.UTF8, "application/json");
                    }
                    else if (callCount == 2)
                    {
                        // Events response
                        req.Content = new StringContent(JsonSerializer.Serialize(new
                        {
                            accepted = 2,
                            rejected = 0,
                            trackingEnabled = true,
                            nextFlushSeconds = 30
                        }), Encoding.UTF8, "application/json");
                    }
                });

            var httpClient = new HttpClient(mockHandler.Object) { BaseAddress = new Uri(_baseUrl) };
            var sdk = new ShreSDK(_tenantId, _appPlatform, _baseUrl);
            var fieldInfo = typeof(ShreSDK).GetField("_httpClient", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            fieldInfo?.SetValue(sdk, httpClient);

            // Act
            var config = await sdk.GetConfigAsync();
            var events = new List<Event>
            {
                new Event { EventId = "evt_001", EventName = "test1", EntityType = "test" },
                new Event { EventId = "evt_002", EventName = "test2", EntityType = "test" }
            };
            var result = await sdk.SendEventsBatchAsync(events);

            // Assert
            Assert.True(config.TrackingEnabled);
            Assert.Equal(2, result.Accepted);
        }

        #endregion
    }
}
