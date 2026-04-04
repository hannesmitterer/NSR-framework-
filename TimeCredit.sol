// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// OpenZeppelin imports (install via npm: @openzeppelin/contracts)
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/// @title TimeCredit – ERC20 token for tracking allocated time credits
/// @notice Deploy on Optimism L2. Minting is restricted to accounts with the MINTER_ROLE.
contract TimeCredit is ERC20, AccessControl, Pausable {
    // ───── Roles ─────
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    /// @dev Constructor sets token name/symbol and assigns admin role to deployer.
    /// @param initialSupply Amount of credits (in wei) minted to the deployer at launch.
    constructor(uint256 initialSupply) ERC20("Time Credit", "TCRED") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);

        // Mint initial supply to the deployer (optional)
        if (initialSupply > 0) {
            _mint(msg.sender, initialSupply);
        }
    }

    // ───── Mint / Burn ─────
    /// @notice Mint new credits to a recipient. Callable only by MINTER_ROLE.
    /// @param to Recipient address.
    /// @param amount Number of tokens (with 18 decimals) to mint.
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) whenNotPaused {
        _mint(to, amount);
    }

    /// @notice Burn credits from caller’s balance.
    /// @param amount Number of tokens to destroy.
    function burn(uint256 amount) external whenNotPaused {
        _burn(msg.sender, amount);
    }

    // ───── Pausing ─────
    /// @notice Pause all token transfers. Callable only by PAUSER_ROLE.
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /// @notice Unpause token transfers. Callable only by PAUSER_ROLE.
    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    // ───── ERC20 Hooks ─────
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override whenNotPaused {
        super._beforeTokenTransfer(from, to, amount);
    }
}
