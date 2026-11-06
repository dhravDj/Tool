#include <iostream>
#include <string>
#include <vector>
#include <memory>

namespace documind {

class TensorNode {
public:
    TensorNode(std::string name, int dimensions) 
        : name_(std::move(name)), dimensions_(dimensions) {}

    virtual ~TensorNode() = default;

    int get_dimensions() const {
        return dimensions_;
    }

private:
    std::string name_;
    int dimensions_;
};

} // namespace documind
