#pragma once
#include <hyprland/src/render/pass/PassElement.hpp>

class CHyprBar;

class CBarPassElement : public IPassElement {
  public:
    struct SBarData {
        CHyprBar* deco = nullptr;
        float     a    = 1.F;
    };

    CBarPassElement(const SBarData& data_);
    virtual ~CBarPassElement() = default;

    virtual std::vector<UP<IPassElement>> draw() override;
    virtual bool                          needsLiveBlur() override;
    virtual bool                          needsPrecomputeBlur() override;
    virtual std::optional<CBox>           boundingBox() override;

    virtual const char*                   passName() override {
        return "CBarPassElement";
    }

    virtual ePassElementType type() override {
        return EK_CUSTOM;
    }

  private:
    SBarData data;
};

class CSnapPreviewPassElement : public IPassElement {
  public:
    struct SSnapData {
        CBox box;
    };

    CSnapPreviewPassElement(const SSnapData& data_);
    virtual ~CSnapPreviewPassElement() = default;

    virtual std::vector<UP<IPassElement>> draw() override;
    virtual bool                          needsLiveBlur() override;
    virtual bool                          needsPrecomputeBlur() override;
    virtual std::optional<CBox>           boundingBox() override;
    virtual bool                          undiscardable() override {
        return true;
    }
    virtual bool                          disableSimplification() override {
        return true;
    }

    virtual const char*                   passName() override {
        return "CSnapPreviewPassElement";
    }

    virtual ePassElementType type() override {
        return EK_CUSTOM;
    }

  private:
    SSnapData data;
};