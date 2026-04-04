// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title SilentBridge
 * @notice On-chain message registry for the Lex Amoris ecosystem
 * @dev Stores message CIDs and metadata with role-based access control
 * 
 * Features:
 * - Message registration with IPFS CID
 * - Event emissions for audit trail
 * - Role-based access (owner, whitelisted nodes)
 * - Rate limiting via cooldown periods
 * - Emergency pause mechanism
 */

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract SilentBridge is Ownable, Pausable {
    
    // =========================================================================
    // State Variables
    // =========================================================================
    
    struct Message {
        string cid;              // IPFS Content Identifier
        address sender;          // Ethereum address of sender
        string nodeId;           // Node ID from Lex Amoris system
        string role;             // Role: RADICE, SILENZIO, NODO
        uint256 timestamp;       // Block timestamp
        string messageType;      // Type of message
        bytes32 contentHash;     // Hash of the message content (for verification)
    }
    
    // Message storage
    Message[] public messages;
    
    // Mapping: sender address => last message timestamp (for rate limiting)
    mapping(address => uint256) public lastMessageTime;
    
    // Mapping: sender address => total messages sent
    mapping(address => uint256) public messageCounts;
    
    // Whitelist: addresses allowed to send messages
    mapping(address => bool) public whitelist;
    
    // Exemptions: addresses exempt from rate limiting
    mapping(address => bool) public exemptions;
    
    // Rate limit cooldown period (seconds)
    uint256 public cooldownPeriod = 60; // 1 minute default
    
    // =========================================================================
    // Events
    // =========================================================================
    
    event MessageRegistered(
        uint256 indexed messageId,
        address indexed sender,
        string nodeId,
        string role,
        string cid,
        uint256 timestamp
    );
    
    event WhitelistUpdated(address indexed account, bool whitelisted);
    event ExemptionUpdated(address indexed account, bool exempted);
    event CooldownPeriodUpdated(uint256 oldPeriod, uint256 newPeriod);
    event EmergencyPause(address indexed by, uint256 timestamp);
    event EmergencyUnpause(address indexed by, uint256 timestamp);
    
    // =========================================================================
    // Constructor
    // =========================================================================
    
    constructor() Ownable(msg.sender) {
        // Owner is automatically whitelisted and exempted
        whitelist[msg.sender] = true;
        exemptions[msg.sender] = true;
    }
    
    // =========================================================================
    // Modifiers
    // =========================================================================
    
    modifier onlyWhitelisted() {
        require(whitelist[msg.sender], "SilentBridge: sender not whitelisted");
        _;
    }
    
    modifier rateLimited() {
        if (!exemptions[msg.sender]) {
            require(
                block.timestamp >= lastMessageTime[msg.sender] + cooldownPeriod,
                "SilentBridge: rate limit exceeded"
            );
        }
        _;
    }
    
    // =========================================================================
    // Core Functions
    // =========================================================================
    
    /**
     * @notice Register a new message on-chain
     * @param cid IPFS Content Identifier
     * @param nodeId Node ID from Lex Amoris system
     * @param role Sender role (RADICE, SILENZIO, NODO)
     * @param messageType Type of message
     * @param contentHash Hash of message content for verification
     * @return messageId The ID of the registered message
     */
    function registerMessage(
        string memory cid,
        string memory nodeId,
        string memory role,
        string memory messageType,
        bytes32 contentHash
    ) 
        external 
        whenNotPaused 
        onlyWhitelisted 
        rateLimited 
        returns (uint256 messageId) 
    {
        // Create message
        Message memory newMessage = Message({
            cid: cid,
            sender: msg.sender,
            nodeId: nodeId,
            role: role,
            timestamp: block.timestamp,
            messageType: messageType,
            contentHash: contentHash
        });
        
        // Store message
        messages.push(newMessage);
        messageId = messages.length - 1;
        
        // Update sender stats
        lastMessageTime[msg.sender] = block.timestamp;
        messageCounts[msg.sender]++;
        
        // Emit event
        emit MessageRegistered(
            messageId,
            msg.sender,
            nodeId,
            role,
            cid,
            block.timestamp
        );
        
        return messageId;
    }
    
    /**
     * @notice Get a message by ID
     * @param messageId The message ID
     * @return The message details
     */
    function getMessage(uint256 messageId) 
        external 
        view 
        returns (Message memory) 
    {
        require(messageId < messages.length, "SilentBridge: message does not exist");
        return messages[messageId];
    }
    
    /**
     * @notice Get total number of messages
     * @return Total message count
     */
    function getMessageCount() external view returns (uint256) {
        return messages.length;
    }
    
    /**
     * @notice Get messages in a range
     * @param startId Start message ID
     * @param count Number of messages to retrieve
     * @return Array of messages
     */
    function getMessages(uint256 startId, uint256 count) 
        external 
        view 
        returns (Message[] memory) 
    {
        require(startId < messages.length, "SilentBridge: invalid start ID");
        
        uint256 endId = startId + count;
        if (endId > messages.length) {
            endId = messages.length;
        }
        
        uint256 resultCount = endId - startId;
        Message[] memory result = new Message[](resultCount);
        
        for (uint256 i = 0; i < resultCount; i++) {
            result[i] = messages[startId + i];
        }
        
        return result;
    }
    
    // =========================================================================
    // Whitelist Management
    // =========================================================================
    
    /**
     * @notice Add address to whitelist
     * @param account Address to whitelist
     */
    function addToWhitelist(address account) external onlyOwner {
        whitelist[account] = true;
        emit WhitelistUpdated(account, true);
    }
    
    /**
     * @notice Remove address from whitelist
     * @param account Address to remove
     */
    function removeFromWhitelist(address account) external onlyOwner {
        whitelist[account] = false;
        emit WhitelistUpdated(account, false);
    }
    
    /**
     * @notice Batch add addresses to whitelist
     * @param accounts Array of addresses to whitelist
     */
    function batchAddToWhitelist(address[] calldata accounts) external onlyOwner {
        for (uint256 i = 0; i < accounts.length; i++) {
            whitelist[accounts[i]] = true;
            emit WhitelistUpdated(accounts[i], true);
        }
    }
    
    // =========================================================================
    // Exemption Management
    // =========================================================================
    
    /**
     * @notice Add address to rate limit exemptions
     * @param account Address to exempt
     */
    function addExemption(address account) external onlyOwner {
        exemptions[account] = true;
        emit ExemptionUpdated(account, true);
    }
    
    /**
     * @notice Remove address from exemptions
     * @param account Address to remove
     */
    function removeExemption(address account) external onlyOwner {
        exemptions[account] = false;
        emit ExemptionUpdated(account, false);
    }
    
    // =========================================================================
    // Rate Limiting Configuration
    // =========================================================================
    
    /**
     * @notice Update cooldown period for rate limiting
     * @param newPeriod New cooldown period in seconds
     */
    function setCooldownPeriod(uint256 newPeriod) external onlyOwner {
        uint256 oldPeriod = cooldownPeriod;
        cooldownPeriod = newPeriod;
        emit CooldownPeriodUpdated(oldPeriod, newPeriod);
    }
    
    // =========================================================================
    // Emergency Controls
    // =========================================================================
    
    /**
     * @notice Pause the contract (emergency only)
     */
    function pause() external onlyOwner {
        _pause();
        emit EmergencyPause(msg.sender, block.timestamp);
    }
    
    /**
     * @notice Unpause the contract
     */
    function unpause() external onlyOwner {
        _unpause();
        emit EmergencyUnpause(msg.sender, block.timestamp);
    }
    
    // =========================================================================
    // View Functions
    // =========================================================================
    
    /**
     * @notice Check if address is whitelisted
     * @param account Address to check
     * @return True if whitelisted
     */
    function isWhitelisted(address account) external view returns (bool) {
        return whitelist[account];
    }
    
    /**
     * @notice Check if address is exempted from rate limits
     * @param account Address to check
     * @return True if exempted
     */
    function isExempted(address account) external view returns (bool) {
        return exemptions[account];
    }
    
    /**
     * @notice Get time until sender can send next message
     * @param account Address to check
     * @return Seconds until next message allowed (0 if ready)
     */
    function getTimeUntilNextMessage(address account) external view returns (uint256) {
        if (exemptions[account]) {
            return 0;
        }
        
        uint256 nextAllowedTime = lastMessageTime[account] + cooldownPeriod;
        if (block.timestamp >= nextAllowedTime) {
            return 0;
        }
        
        return nextAllowedTime - block.timestamp;
    }
}
